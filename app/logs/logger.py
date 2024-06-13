import logging

# Function for logging task
def configure_logging():

    # Set the Werkzeug logger level to ERROR
    logging.getLogger('werkzeug').setLevel(logging.ERROR)

    # Set up general logging
    logging.basicConfig(
        filename='pdfbot.log',
        level=logging.ERROR,
        format='%(asctime)s - %(levelname)s - %(filename)s - %(lineno)d - %(message)s'
    )

    return logging.getLogger(__name__)
