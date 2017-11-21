from django.shortcuts import render
from .models import AgentsArea
from .models import AgentsData
from .models import LastUpdateAgentsDate
from .api_connection import EmptyRequest
from .api_connection import RequestAgentsInPeriod
from .api_connection import RequestAgentsRawData
from project_indicators.views import clean_url
from quero_cultura.views import ParserYAML
from datetime import datetime
from celery.decorators import task

DEFAULT_INITIAL_DATE = "2012-01-01 00:00:00.000000"
SP_URL = "http://spcultura.prefeitura.sp.gov.br/api/"
DEFAULT_YEAR = 2013
CURRENT_YEAR = datetime.today().year + 1


def index(request):
    # AgentsArea.drop_collection()
    # AgentsData.drop_collection()
    # LastUpdateAgentsDate.drop_collection()
    # populate_agent_data()
    return render(request, 'agents_indicators/agents-indicators.html')


# @task(name="populate_agent_data")
def populate_agent_data():
    if len(LastUpdateAgentsDate.objects) == 0:
        LastUpdateAgentsDate(DEFAULT_INITIAL_DATE).save()

    size = LastUpdateAgentsDate.objects.count()
    last_update = LastUpdateAgentsDate.objects[size - 1].create_date

    parser_yaml = ParserYAML()
    urls = parser_yaml.get_multi_instances_urls

    for url in urls:
        if url == SP_URL:
            request = EmptyRequest()
            for year in range(DEFAULT_YEAR, CURRENT_YEAR):
                single_request = RequestAgentsInPeriod(year, url)
                request.data += single_request.data
            request = request.data
            new_url = clean_url(url)
        else:
            request = RequestAgentsRawData(last_update, url).data
            new_url = clean_url(url)

        for agent in request:
            date = agent["createTimestamp"]['date']
            AgentsData(new_url, str(agent['type']['name']), date).save()
            for area in agent["terms"]["area"]:
                AgentsArea(new_url, area).save()

    LastUpdateAgentsDate(str(datetime.now())).save()
