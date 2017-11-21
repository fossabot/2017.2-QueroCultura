from datetime import datetime
from django.shortcuts import render
from .api_connections import RequestSpacesRawData
from .models import SpaceData
from .models import LastUpdateDate
from project_indicators.views import clean_url
from quero_cultura.views import ParserYAML
from quero_cultura.views import get_metabase_url
from celery.decorators import task
from .models import OccupationArea

DEFAULT_INITIAL_DATE = "2012-01-01 00:00:00.000000"

# Get graphics urls from metabase
# To add new graphis, just add in the metabase_urls variable
view_type = "question"
metabase_urls = [{'id':1, 'url':get_metabase_url(view_type, 2)},
                 {'id':2, 'url':get_metabase_url(view_type, 4)},
                 {'id':3, 'url':get_metabase_url(view_type, 3)},
                 {'id':4, 'url':get_metabase_url(view_type, 7)},
                 {'id':5, 'url':get_metabase_url(view_type, 6)}]

def index(request):
    return render(request, 'space_indicators/space-indicators.html', {'metabase_urls':metabase_urls})

def graphicDetail(request, metabase_url_id):
    metabase_url = metabase_urls[int(metabase_url_id) - 1]
    return render(request,'space_indicators/graphicDetail.html',{'metabase_url': metabase_url}) 

@task(name="populate_space_data")
def populate_space_data():
    if len(LastUpdateDate.objects) == 0:
        LastUpdateDate(DEFAULT_INITIAL_DATE).save()

    size = LastUpdateDate.objects.count()
    last_update = LastUpdateDate.objects[size - 1].create_date

    parser_yaml = ParserYAML()
    urls = parser_yaml.get_multi_instances_urls

    for url in urls:
        request = RequestSpacesRawData(last_update, url).data
        new_url = clean_url(url)
        for space in request:
            date = space["createTimestamp"]['date']
            SpaceData(new_url, space['name'], date,
                      space['type']['name']).save()
            for area in space["terms"]["area"]:
                OccupationArea(new_url, area).save()

    LastUpdateDate(str(datetime.now())).save()
