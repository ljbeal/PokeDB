import re


def remove_sql_illegal_characters(input_string: str) -> str:
    # Remove spaces and special symbols except underscores
    cleaned_string = re.sub(r'[^a-zA-Z0-9_]', '', input_string)

    return cleaned_string


if __name__ == "__main__":
    input_string = "my table-n'ame!_123"
    cleaned_identifier = remove_sql_illegal_characters(input_string)
    print(cleaned_identifier)
