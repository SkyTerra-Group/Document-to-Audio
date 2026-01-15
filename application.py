# This file is required for AWS Elastic Beanstalk deployment
# Elastic Beanstalk looks for application.py as the entry point

from app import app as application

if __name__ == "__main__":
    application.run()