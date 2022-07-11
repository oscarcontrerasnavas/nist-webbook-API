import os
import json

from pymongo import MongoClient
from twisted.web.error import Error
from dotenv import load_dotenv
load_dotenv()

from scrapyrt.resources import CrawlResource, ServiceResource



class CheckDatabaseBeforeCrawlResource(CrawlResource):

    def render_GET(self, request, **kwargs):

        # Get the url parameters
        api_params = dict(
            (name.decode('utf-8'), value[0].decode('utf-8'))
            for name, value in request.args.items()
        )
            
        try:
            cas = json.loads(api_params["crawl_args"])["cas"]
            client = MongoClient(os.environ.get("MONGO_URI"))
            db = client[os.environ.get("MONGO_DB")]
        except Exception as e:
            return 
        collection_name = "substances"
        substance = db[collection_name].find_one({"cas":cas}, {"_id":0})
        if substance:
            response = {
            "status": "ok",
            "items": [substance],
            }

            return response
        
        return super(CheckDatabaseBeforeCrawlResource, self).render_GET(
        request, **kwargs)


class SubstancesResource(ServiceResource):
    # Return a list of name: cas pairs
    def render_GET(self, request, **kwargs): 
        isLeaf = True

        try:
            client = MongoClient(os.environ.get("MONGO_URI"))
            db = client[os.environ.get("MONGO_DB")]
        except ValueError as e:
            raise Error('400', str(e))

        api_params = dict(
            (name.decode('utf-8'), value[0].decode('utf-8'))
            for name, value in request.args.items()
        )

        page = api_params['page'] if 'page' in api_params else 1
        per_page = api_params['per_page'] if 'per_page' in api_params else 20

        collection_name = "substances"
        substances = db[collection_name].find({}, {
            "_id" : 0,
            "name" : 1, 
            "cas" : 1, 
            "formula" : 1,
            "molecular_weight" : 1,
            "image" : 1,
            
        }).skip((page - 1) * per_page).limit(per_page)
        total_substances = db[collection_name].count_documents({})

        substances = list(substances)
        response = {
            "status": "ok",
            "current_page": page,
            "items_per_page": per_page,
            "total_items": total_substances,
            "items" : substances,
        }

        return response