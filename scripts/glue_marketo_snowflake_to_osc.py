import logging
import argparse
from tasks.aws_api_io import MarketoETL, SecretsManagerIO
from tasks.snowflake_io import snowflake_io
from tasks.osc_io import osc_io
from tasks.utils import get_pipeline_execution_id, get_max_dynamics_datetime
import concurrent.futures
import json

# Constants for execution stage and state
EXECUTION_STAGE = 0
EXECUTION_STATE = 1

# Logger setup class
class setLogger:
    def __init__(self, logger: logging.Logger = None):
        # Configure logging format and level
        logging.basicConfig(
            format='%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
            datefmt='%Y-%m-%d:%H:%M:%S',
            level=logging.INFO
        )
        self.logger = logging.getLogger() if logger is None else logger
        console_handler = logging.StreamHandler()
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(console_handler)

    def getLogger(self):
        # Return the configured logger
        return self.logger

# Argument parser class for command-line options
class Argunents:
    def __init__(self):
        self.args: dict = None
        self.arg_parse = argparse.ArgumentParser()
        # Define all required and optional arguments
        # self.arg_parse.add_argument('--conf_table', help='Marketo Configuration Table', type=str, required=True)
        # self.arg_parse.add_argument('--ops_table', help='Marketo Operations table', type=str, required=True)
        self.arg_parse.add_argument('--env', help="environment (dev, stage, prod)", type=str, required=True)
        self.arg_parse.add_argument('--bucket_name', help="s3 bucket to put api results", type=str, required=True)
        self.arg_parse.add_argument('--secret_name', help="secret for marketoETL", type=str, required=True)
        self.arg_parse.add_argument('--pipelineIds', help="pipelineIds to execute for", type=str, required=False, default="*")
        self.arg_parse.add_argument('--job_stage', help="job stage for this glue job", type=str, required=False, default="marketoETL_to_snowflake")
        self.arg_parse.add_argument('--region_name', help="region to use", type=str, required=False, default="us-east-2")
        self.arg_parse.add_argument('--source', help="source of the data", type=str, required=False, default="zoomInfo")
        self.arg_parse.add_argument('--job_name', help="name of the glue job", type=str, required=False, default="glue_marketo_snowflake_to_osc")
        self.arg_parse.add_argument('--max_workers', help="max workers for threading", type=int, required=False, default=5)

    def set_args(self):
        # Parse arguments from command line
        args, unknown = self.arg_parse.parse_known_args()
        return args

# Function to process a single pipeline
def process_pipeline(
    pipeline_id: str,
    logger: logging.Logger,
    args_u: argparse.Namespace
):
    logger.info("Processing pipeline %s" % pipeline_id)
    execution_id = get_pipeline_execution_id()
    logger.info('Step: Get latest watermark')
    try:
        # Get the latest watermark for the pipeline
        watermark_value = MarketoETL(
            args=args_u,
            logger=logger
        ).get_latest_watermark(
            pipeline_id=pipeline_id,
        )
    except Exception as e:
        logger.error(f"Error getting watermark value: {e}")
        return

    logger.info('Step: Get secret data')
    try:
        # Retrieve secret data from AWS Secrets Manager
        secret_data = SecretsManagerIO(
            args=args_u,
            logger=logger
        ).get_secret(
            args_u.secret_name
        )
    except Exception as e:
        logger.error(f"Error getting secret data: {e}")
        return

    logger.info('Step: Get data from zoominfo from snowflake')
    zoomInfo_rows = None
    try:
        # Fetch entity data from Snowflake
        zoomInfo_rows = snowflake_io(
            args=args_u,
            logger=logger,
            pipeline_id=pipeline_id,
            execution_id=execution_id
        ).get_entity_data(
            watermark=watermark_value,
            secret_data=secret_data,
            source=args_u.source
        )
    except Exception as e:
        logger.error(f"Error getting data from snowflake: {e}")
        return

    if zoomInfo_rows is None:
        logger.info('No data to process')
        return

    logger.info('Step: zoomInfo puts payload data')
    for row in zoomInfo_rows:
        payload = None
        try:
            # Store item in Snowflake
            payload = MarketoETL(
                args=args_u,
                logger=logger
            ).put_item(row)
        except Exception as e:
            logger.error(f"Error putting execution data to OSC: {e}")
            return
        oscresponse = None
        try:
            # Send payload data to OSC
            oscresponse = osc_io(
                args=args_u,
                logger=logger,
                pipeline_id=pipeline_id,
                execution_id=execution_id
            ).create_OSC_Account(
                payload_data=payload
            )
        except Exception as e:
            logger.error(f"Error putting payload data to OSC: {e}")
            return

# Main function to orchestrate pipeline processing
def main():
    logger = setLogger().getLogger()
    args_u = Argunents().set_args()

    global env
    env = args_u.env
    global job_stage
    job_stage = args_u.job_stage
    # Determine pipeline IDs to process
    if args_u.pipelineIds is None or args_u.pipelineIds == "*":
        pipeline_ids = MarketoETL(
            args=args_u,
            logger=logger
        ).get_items(
            table_name=args_u.conf_table,
            key={"integrationPattern": args_u.source, "consumeFlag": 1},
            fields="pipelineId"
        )
        logger.info(pipeline_ids)
        pipeline_ids = [item['pipelineId'] for item in pipeline_ids]
    else:
        pipeline_ids = list(args_u.pipelineIds.split(','))
    logger.info("pipelines to execute for this %s" % pipeline_ids)
    # Use ThreadPoolExecutor to process pipelines concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=args_u.max_workers) as executor:
        futures = [executor.submit(process_pipeline, pipeline_id, logger, args_u) for pipeline_id in pipeline_ids]
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logger.error(f"Pipeline processing generated an exception: {e}")

# Entry point for script execution
if __name__ == "__main__":
    main()

