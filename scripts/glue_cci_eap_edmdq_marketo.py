
import urllib3.util.ssl_
 
if not hasattr(urllib3.util.ssl_, 'DEFAULT_CIPHERS'):
    # Define a secure default cipher string
    urllib3.util.ssl_.DEFAULT_CIPHERS = (
        "ECDHE+AESGCM:ECDHE+CHACHA20:ECDHE+AES256:ECDHE+AES128:!aNULL:!eNULL:!MD5"
    )

import logging
import argparse
from tasks.aws_api_io import MarketoETL, SecretsManagerIO
from tasks.aws_snowflake_io import AwsSnowflakeIo
from tasks.osc_account_io import OscAccountIo
from tasks.utils import get_pipeline_execution_id
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
        self.arg_parse.add_argument('--env', help="environment (dev, stage, prod)", type=str, required=True)
        self.arg_parse.add_argument('--secret_name', help="secret for marketoETL", type=str, required=True)
        self.arg_parse.add_argument('--pipelineIds', help="pipelineIds to execute for", type=str, required=False, default="*")
        self.arg_parse.add_argument('--job_stage', help="job stage for this glue job", type=str, required=False, default="marketoETL_to_snowflake")
        self.arg_parse.add_argument('--region_name', help="region to use", type=str, required=False, default="us-east-2")
        self.arg_parse.add_argument('--source', help="source of the data", type=str, required=False, default="zoomInfo")
        self.arg_parse.add_argument('--job_name', help="name of the glue job", type=str, required=False, default="glue_cci_eap_edmdq_marketo")
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
            args_u.env+"/cci-eap-edmdq-marketo/DM_Snowflake_OSC_Marketo_ETL"
        )
    except Exception as e:
        logger.error(f"Error getting secret data: {e}")
    if args_u.env == 'dev':
        secret_data = {
            "DM_Snowflake_token_url" : "https://login.microsoftonline.com/3c614fdd-6711-42ae-a368-f96ab9460598/oauth2/v2.0/token",
            "DM_Snowflake_auth_scope" : "https://crowncastle.com/bde23c60-815b-4bcb-86ff-95b5d57bf3fd-SnowflakeOAuthForServiceAccounts/.default",
            "DM_Snowflake_client_ID" : "f9d84658-0724-46b8-80cc-7719d413ef88",
            "DM_Snowflake_client_secret"  : "VT7939Jpp5lgBfpNyaLd2rYoCpGhIQsMj2xStgWyGrc=",
            "DM_Snowflake_grant_type" : "client_credentials",
            "DM_Snowflake_Database" : "CDWDEV",
            "DM_Snowflake_Account" : "ccic-mainnew",
            "DM_Snowflake_Azure_User_ID" : "0baab986-1a68-4191-953b-147d8fc0c71c",
            "DM_Snowflake_Role" : "DATA_MANAGEMENT_RO_ROLE",
            "DM_Snowflake_Warehouse" : "BUSINESS_REPORTING_WH",
            "DM_OSC_API_Account_Create" : "https://crowncastle-dev.crm.dynamics.com/api/data/v9.1/accounts",
            "DM_OSC_API_Token_Create_Url" : "https://login.microsoftonline.com/3c614fdd-6711-42ae-a368-f96ab9460598/oauth2/token",
            "DM_OSC_API_Client_ID" : "db80b2c6-bfdc-49af-9627-f63b73b85ada",
            "DM_OSC_API_Client_Secret" : "PBTRXCa6lnE_-G6M5S-e8H5T0ek5.A3E-D",
            "DM_OSC_API_Scope" : "https://vault.azure.net/.default",
            "DM_OSC_API_Grant_Type" : "client_credentials",
            "DM_OSC_API_Resource" : "https://crowncastle-dev.crm.dynamics.com"
        }
    elif args_u.env == 'prod':
        secret_data = {
            "DM_Snowflake_token_url" : "https://login.microsoftonline.com/3c614fdd-6711-42ae-a368-f96ab9460598/oauth2/v2.0/token",
            "DM_Snowflake_auth_scope" : "https://crowncastle.com/bde23c60-815b-4bcb-86ff-95b5d57bf3fd-SnowflakeOAuthForServiceAccounts/.default",
            "DM_Snowflake_client_ID" : "625e68db-fb5d-4b5e-96e6-0a5dc0eb62da",
            "DM_Snowflake_client_secret"  : "scoUzM34N+72s8ArjShRYARdwUcgr9ATJ8cT99IdjpA=",
            "DM_Snowflake_grant_type" : "client_credentials",
            "DM_Snowflake_Database" : "CDWPRD",
            "DM_Snowflake_Account" : "ccic-mainnew",
            "DM_Snowflake_Azure_User_ID" : "9e33ff8b-da14-46ce-bcfb-d2bc6cdf9f23",
            "DM_Snowflake_Role" : "DATA_MANAGEMENT_RO_ROLE",
            "DM_Snowflake_Warehouse" : "BUSINESS_REPORTING_WH",
            "DM_OSC_API_Account_Create" : "https://crowncastle.crm.dynamics.com/api/data/v9.1/accounts",
            "DM_OSC_API_Token_Create_Url" : "https://login.microsoftonline.com/3c614fdd-6711-42ae-a368-f96ab9460598/oauth2/token",
            "DM_OSC_API_Client_ID" : "d9f4fcfc-a3b0-49e7-8a74-c0770dd6e381",
            "DM_OSC_API_Client_Secret" : "CqZoRq_EzmvoEvP-_oN.s8.z21~J7p7ZeC",
            "DM_OSC_API_Scope" : "https://vault.azure.net/.default",
            "DM_OSC_API_Grant_Type" : "client_credentials",
            "DM_OSC_API_Resource" : "https://crowncastle.crm.dynamics.com"
            }
    else:
        secret_data = None    

    logger.info('Step: Get data from zoominfo from snowflake')
    zoomInfo_rows = None
    snowfalke_connect = None
    try:
        snowfalke_connect = AwsSnowflakeIo(
            args=args_u,
            logger=logger,
            pipeline_id=pipeline_id  #,
            # execution_id=execution_id
        ).return_connection(secret_data)
    except Exception as e:
        logger.info(f"Error getting snowflake connection: {e}")
    try:
        # Fetch entity data from Snowflake
        zoomInfo_rows = AwsSnowflakeIo(
            args=args_u,
            logger=logger,
            pipeline_id=pipeline_id  #,
#            execution_id=execution_id
        ).transfer_entity_data(
            snowfalke_connect
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
            ).put_item(row=row)
        except Exception as e:
            logger.error(f"Error putting execution data to OSC: {e}")
            return
        oscresponse = None
        try:
            # Send payload data to OSC
            oscresponse = OscAccountIo(
                args=args_u,
                logger=logger,
                pipeline_id=pipeline_id
            ).create_osc_account(
                payload_data=payload,
                secret_data=secret_data
            )
        except Exception as e:
            logger.error(f"Error putting payload data to OSC: {e}")
            return
        accountnumber = oscresponse.get('accountnumber')
        if  accountnumber is not None:
            try:
                AwsSnowflakeIo(
                    args=args_u,
                    logger=logger,
                    pipeline_id=pipeline_id
                ).update_osc_account(connect=snowfalke_connect,
                                     accountnumber=accountnumber, 
                                     zoominfo_company_id=row[0])
            except Exception as e:
                logger.error(f"Error updating OSC account in Snowflake: {e}")
                return
    snowfalke_connect.close()

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
        )
        logger.info(pipeline_ids)
        # pipeline_ids = [item['pipelineId'] for item in pipeline_ids]
    else:
        pipeline_ids = list(args_u.pipelineIds.split(','))
    logger.info("pipelines to execute for this %s" % pipeline_ids)
    # Use ThreadPoolExecutor to process pipelines concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=args_u.max_workers) as executor:
        futures = [executor.submit(process_pipeline, '1', logger, args_u)] 
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logger.error(f"Pipeline processing generated an exception: {e}")

# Entry point for script execution
if __name__ == "__main__":
    main()

