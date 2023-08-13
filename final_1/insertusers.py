import pymongo

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["adb_project"]
mycollection1=mydb['login_data']

name="Rajan"
pass1="123"

obj1={
    "username":name,
    "password":pass1
}

x = mycollection1.insert_one(obj1)