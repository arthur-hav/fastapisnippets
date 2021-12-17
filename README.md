# Fast Api Snippets

Small usable code examples.

## nest.py

Provides a redis handler that stores `BaseModel`s in flat redis structure and rebuild them from id. Although this could
be trivially implemented by saving and loading json representations, this handler decomposes the model into fields and
store individual keys in order to improve overall performance in handling big objects partial updates and sub-item gets.

## main.py

Minimal example of a REST api using the features.