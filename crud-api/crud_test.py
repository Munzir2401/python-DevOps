import requests

BASE = "http://127.0.0.1:8000"

print("\n Server Check:", requests.get(BASE).json())

print("\n Creating item...")
r = requests.post(BASE + "/items", json={"name": "Laptop", "description": "Gaming laptop"})
print("Created:", r.json())
item_id = r.json().get("id")

print("\n Getting all items...")
print(requests.get(BASE + "/items").json())

print("\n Updating item...")
print(requests.put(BASE + f"/items/{item_id}", json={"name": "Laptop Pro", "description": "Upgraded version"}).json())

print("\n Deleting item...")
print(requests.delete(BASE + f"/items/{item_id}").json())

print("\n Final Items:", requests.get(BASE + "/items").json())

