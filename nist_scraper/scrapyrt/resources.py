import os
import json

from pymongo import MongoClient
from dotenv import load_dotenv
load_dotenv()

from scrapyrt.resources import CrawlResource



class CheckDatabaseBeforeCrawlResource(CrawlResource):

    def render_GET(self, request, **kwargs):

        # Get the url parameters
        api_params = dict(
            (name.decode('utf-8'), value[0].decode('utf-8'))
            for name, value in request.args.items()
        )
            
        try:
            cas = json.loads(api_params["crawl_args"])["cas"]
            collection_name = "substances"
            client = MongoClient(os.environ.get("MONGO_URI"))
            db = client[os.environ.get("MONGO_DB")]
        except:
            return super(CheckDatabaseBeforeCrawlResource, self).render_GET(
                request, **kwargs)

        substance = db[collection_name].find_one({"cas":cas}, {"_id":0})
        if substance:
            response = {
            "status": "ok",
            "items": [substance],
            }

            return response
        
        return super(CheckDatabaseBeforeCrawlResource, self).render_GET(
        request, **kwargs)