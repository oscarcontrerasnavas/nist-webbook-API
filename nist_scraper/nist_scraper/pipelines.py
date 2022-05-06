# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import pymongo
from itemadapter import ItemAdapter
import logging


class MongoPipeline:
    collection_name = "substances"

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get("MONGO_URI"),
            mongo_db=crawler.settings.get("MONGO_DB"),
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        duplicate = (
            self.db[self.collection_name].count_documents({"cas": item["cas"]}) > 0
        )
        if not duplicate:
            self.db[self.collection_name].insert_one(ItemAdapter(item).asdict())
        else:
            logging.info(
                'The item "{}" is already in the database'.format(item["name"])
            )
        return item
