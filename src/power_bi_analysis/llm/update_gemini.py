import sys

with open('gemini_client.py', 'r') as f:
    lines = f.readlines()

# Find insertion point for new generation methods (before _get_system_prompt)
insert_idx = None
for i, line in enumerate(lines):
    if line.strip().startswith('def _get_system_prompt'):
        insert_idx = i
        break

if insert_idx is None:
    print('Could not find _get_system_prompt')
    sys.exit(1)

# New generation methods
generate_sql_schema = '''    def generate_sql_schema(self, metadata_text: str, file_name: str) -> str:
        """
        Generate SQL schema (DDL) using Gemini.
        """
        prompt = self._create_sql_schema_prompt(metadata_text, file_name)

        try:
            model = genai.GenerativeModel(
                model_name=self._model,
                system_instruction=self._get_sql_schema_system_prompt()
            )
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=4096,
                )
            )
            return response.text
        except Exception as e:
            return f"Error generating SQL schema: {str(e)}"
'''

generate_data_dictionary = '''    def generate_data_dictionary(self, metadata_text: str, file_name: str) -> str:
        """
        Generate data dictionary using Gemini.
        """
        prompt = self._create_data_dictionary_prompt(metadata_text, file_name)

        try:
            model = genai.GenerativeModel(
                model_name=self._model,
                system_instruction=self._get_data_dictionary_system_prompt()
            )
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,
                    max_output_tokens=4096,
                )
            )
            return response.text
        except Exception as e:
            return f"Error generating data dictionary: {str(e)}"
'''

# Insert generation methods
lines.insert(insert_idx, generate_data_dictionary + '\n')
lines.insert(insert_idx, generate_sql_schema + '\n')

# Find insertion point for prompt methods (after _create_sml_prompt)
prompt_insert_idx = None
for i, line in enumerate(lines):
    if line.strip().startswith('def _create_sml_prompt'):
        # find the line after this method (next def or end of class)
        for j in range(i+1, len(lines)):
            if lines[j].strip().startswith('def ') or lines[j].strip().startswith('class '):
                prompt_insert_idx = j
                break
        if prompt_insert_idx is None:
            prompt_insert_idx = len(lines)
        break

if prompt_insert_idx is None:
    print('Could not find _create_sml_prompt')
    sys.exit(1)

# Prompt methods from anthropic_client.py
prompt_methods = '''    def _get_sql_schema_system_prompt(self) -> str:
        """System prompt for SQL schema generation."""
        return """You are a database architect specializing in SQL schema design.
Your task is to convert metadata from a business intelligence file into a SQL Data Definition Language (DDL) schema.

The SQL should be compatible with a modern SQL database (PostgreSQL dialect preferred).
Include:
1. CREATE TABLE statements with appropriate data types
2. Primary key and foreign key constraints where relationships exist
3. Column comments/descriptions
4. Indexes on foreign keys and frequently queried columns
5. Appropriate schema name (use 'analytics' or a suitable schema)

Output ONLY the SQL DDL statements. No explanations, no markdown formatting.
Ensure SQL syntax is valid and follows best practices."""

    def _create_sql_schema_prompt(self, metadata_text: str, file_name: str) -> str:
        """Create prompt for SQL schema generation."""
        return f"""Convert the following metadata from '{file_name}' into a SQL DDL schema.

METADATA:
{metadata_text}

Generate CREATE TABLE statements with appropriate data types, primary keys, foreign keys, and indexes.
Include column comments to document each column's purpose.
Use PostgreSQL-compatible syntax.
If there are relationships between tables, add FOREIGN KEY constraints.
Name the schema 'analytics' or choose an appropriate schema name.

Output only the SQL statements, no additional text."""

    def _get_data_dictionary_system_prompt(self) -> str:
        """System prompt for data dictionary generation."""
        return """You are a data governance specialist.
Your task is to create a comprehensive data dictionary from metadata.

The data dictionary should include:
1. Table name and description
2. Column names, data types, and descriptions
3. Relationships between tables
4. Business definitions of key metrics and calculations
5. Data lineage and source information
6. Data quality rules and constraints

Format the output as a well-structured markdown document with clear sections.
Use tables for column listings where appropriate.
Write for a mixed audience of business and technical stakeholders."""

    def _create_data_dictionary_prompt(self, metadata_text: str, file_name: str) -> str:
        """Create prompt for data dictionary generation."""
        return f"""Create a comprehensive data dictionary from the following metadata of '{file_name}'.

METADATA:
{metadata_text}

The data dictionary should include:
1. Overview of the dataset/report
2. Table-level descriptions
3. Column-level details (name, data type, description, business meaning)
4. Relationships between tables
5. Key metrics and calculations with business definitions
6. Data sources and lineage
7. Data quality notes and constraints

Format as a markdown document with clear headings, tables, and bullet points.
Aim for clarity and completeness to serve both business and technical users."""
'''

# Insert prompt methods
lines.insert(prompt_insert_idx, prompt_methods + '\n')

# Write back
with open('gemini_client.py', 'w') as f:
    f.writelines(lines)

print('Updated gemini_client.py')