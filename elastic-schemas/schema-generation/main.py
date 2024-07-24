import json

import requests

schemas = [
  {'file_name': 'digital-specimen.json',
   'url': 'https://schemas.dissco.tech/schemas/fdo-type/digital-specimen/0.3.0/digital-specimen.json'},
  {'file_name': 'digital-media.json',
   'url': 'https://schemas.dissco.tech/schemas/fdo-type/digital-media/0.3.0/digital-media.json'},
  {'file_name': 'annotation.json',
   'url': 'https://schemas.dissco.tech/schemas/fdo-type/annotation/0.3.0/annotation.json'}
]


def fetch_json_schema(endpoint):
  response = requests.get(endpoint)
  response.raise_for_status()  # Ensure we notice bad responses
  return response.json()


def main():
  for schema in schemas:
    print(f'Generating schema for {schema.get("file_name")}')
    json_schema = fetch_json_schema(schema.get('url'))
    mapping_result = walk_json(json_schema)
    full_index = {
      'settings': {
        'index': {
          "mapping": {
            "total_fields": {
              "limit": 2000
            }
          },
          'number_of_shards': 5,
          'number_of_replicas': 1
        }
      },
      'mappings': {
        'dynamic': 'false',
        'properties': mapping_result
      }
    }
    write_dict_to_file(full_index, schema.get('file_name'))
    print(f'Schema for {schema.get("file_name")} generated successfully')


def write_dict_to_file(dict_data, filename):
  with open(f'../{filename}', 'w') as json_file:
    json.dump(dict_data, json_file, indent=4)


def walk_json(json_schema):
  mapping = {}
  if json_schema.get('properties'):
    for property_name in json_schema.get('properties'):
      json_property = json_schema.get('properties').get(property_name)
      if json_property.get('type') == 'array':
        items = json_property.get('items')
        if items.get('$ref'):
          ref = items.get('$ref')
          array_schema = fetch_json_schema(ref)
          nested_properties = walk_json(array_schema)
          mapping[property_name] = {
            'properties': nested_properties
          }
        elif items.get('type') == 'object':
          nested_properties = walk_json(items)
          mapping[property_name] = {
            'properties': nested_properties
          }
      elif json_property.get('type') == 'object':
        if json_property.get('$ref'):
          ref = json_property.get('$ref')
          object_schema = fetch_json_schema(ref)
        else:
          object_schema = json_property
        nested_properties = walk_json(object_schema)
        mapping[property_name] = {
          'properties': nested_properties
        }
      else:
        mapping[property_name] = generate_property_mapping(json_property)
    return mapping
  elif json_schema.get('oneOf'):
    for one_of_object in json_schema.get('oneOf'):
      mapping.update(walk_json(one_of_object))
    return mapping


def generate_property_mapping(json_property):
  json_type = json_property.get('type')
  if json_property.get('enum'):
    return {
      'type': 'keyword'
    }
  elif json_property.get('const'):
    return {
      'type': 'constant_keyword',
      'value': json_property.get('const')
    }
  elif json_property.get('format') and json_property.get(
      'format') == 'date-time':
    return {
      'type': 'date'
    }
  elif json_type == 'string':
    return {
      'type': 'text',
      'fields': {
        'keyword': {
          'type': 'keyword',
          "ignore_above": 256
        }
      }
    }
  elif json_type == 'boolean':
    return {
      'type': 'boolean'
    }
  elif json_type == 'integer':
    return {
      'type': 'integer'
    }
  elif json_type == 'number':
    return {
      'type': 'float'
    }


if __name__ == "__main__":
  main()
