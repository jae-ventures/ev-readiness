from dotenv import load_dotenv
import os

load_dotenv()

AFDC_API_KEY = os.getenv('AFDC_API_KEY')
CENSUS_API_KEY = os.getenv('CENSUS_API_KEY')