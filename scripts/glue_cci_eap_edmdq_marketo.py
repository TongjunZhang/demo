import sys
import logging
from tasks.cci_eap_edmdq_marketo import main as match_main_process
import argparse


class Arguments:
    def __init__(self):
        self.arg_parse = argparse.ArgumentParser()
        self.arg_parse.add_argument('--secret_name', help='Aws Secret Name', type=str, required=True)
        self.arg_parse.add_argument('--vendor_name', help='Vendor Name', type=str, required=True)
        self.arg_parse.add_argument('--bucket', help='S3 Bucket Name', type=str, required=True)
        self.arg_parse.add_argument('--region_name', help='Region Name', type=str, required=True)
        self.arg_parse.add_argument('--dynamodb_table_name', help='DynamoDB Table Name', type=str, required=True)
        self.arg_parse.add_argument('--ssh_secret_name', help='SSH Secret Name', type=str, required=True)

    def set_args(self):
        args, unknown = self.arg_parse.parse_known_args()
        return args


class LoggerInitializer:
    def __init__(self):
        self.logger = None

    def initialize_logger(self):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        logging.basicConfig(
            format='%(asctime)s - %(levelname)s:%(filename)s:%(lineno)d:%(message)s',
            level=logging.INFO, 
            encoding='utf-8'
        )
        return self.logger


def main():
    logger = LoggerInitializer().initialize_logger()
    try: 
        args = Arguments().set_args()
        match_main_process(
            args=args, 
            logger=logger
            )
    except Exception as e:
        logger.error(f"Failed to execute match process: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
