import yaml
import os

def yaml_metadata_to_json(
	yaml_dir: str = "./data/yaml",
	output_json_dir: str = "./data/json"
	):


	"""
	Converts YAML metadata to JSON
	"""
	# Check the existence of the directory
	os.makedirs(output_json_path, exist_ok=True)
	
	for file in os.scandir(yaml_dir):
		with open(os.path.join(yaml_dir,file.name), "r", encoding="utf-8") as file:
    		entity = yaml.safe_load(file)

		# JSON export
	    base_name = os.path.splitext(file.name)[0]
	    json_filepath = os.path.join(output_json_path, f"{base_name}.json")
	    with open(json_filepath, "w", encoding="utf-8") as json_file:
	        json.dump(entity, json_file, indent=2, ensure_ascii=False)

    print("JSON conversion completed.")    

    return None