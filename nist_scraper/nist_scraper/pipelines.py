# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import pymongo
import logging
import os
from itemadapter import ItemAdapter
from dotenv import load_dotenv

load_dotenv()


class MongoPipeline:
    collection_name = "substances"

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=os.environ.get("MONGO_URI"),
            mongo_db=os.environ.get("MONGO_DB"),
        )

    # def open_spider(self, spider):
    #     self.client = pymongo.MongoClient(self.mongo_uri)
    #     self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):

        try:
            self.client = pymongo.MongoClient(self.mongo_uri)
            self.db = self.client[self.mongo_db]
        except:
            logging.info("Error connecting with database")
            return item

        has_image = "image" in item.keys()
        duplicate = (
            self.db[self.collection_name].count_documents({"cas": item["cas"]}) > 0
        )
        if has_image and not duplicate:
            self.db[self.collection_name].insert_one(ItemAdapter(item).asdict())
        else:
            logging.info(
                'The item "{}" is already in the database'.format(item["name"])
            )
        return item
