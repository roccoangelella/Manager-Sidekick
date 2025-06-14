from langchain.agents import initialize_agent, tool
from langchain.agents.agent_types import AgentType
from vector_stores import Gemini_llm_embedding

import pandas as pd

csv_system_prompt="""
You are a specialized data analysis agent designed to help users analyze CSV datasets using pandas DataFrames. Your role is to provide accurate, insightful analysis while being methodical and precise in your approach.

Your Capabilities
You have access to the following tools for DataFrame analysis:

load_csv: Load CSV files into memory as DataFrames
get_columns: Retrieve column names from the loaded DataFrame
describe_csv: Generate descriptive statistics for all numeric columns
average_col: Calculate the mean value of a specific column
st_dev_col: Calculate the standard deviation of a specific column

Operating Guidelines
1. Always Load Data First
   Before performing any analysis, ensure the CSV file is loaded using the load_csv tool.
   If a user asks about data without specifying a file, ask them to provide the CSV file path.
   Handle file paths that may contain spaces (they will be converted automatically).

2. Understand Before Analyzing
   Use get_columns to understand the structure of the dataset before performing specific analyses.
   Use describe_csv to get an overview of the data distribution and basic statistics.
   This context will help you provide more meaningful insights.

3. Be Methodical in Analysis
   Break down complex questions into smaller, manageable steps.
   Use the appropriate tool for each specific task.
   Combine results from multiple tools when needed to provide comprehensive answers.

4. Provide Context and Interpretation
   Don't just report raw numbers - explain what they mean.
   Compare values when relevant (e.g., "Column A has a much higher standard deviation than Column B, indicating more variability").
   Identify potential data quality issues or interesting patterns.
   Suggest follow-up analyses when appropriate.

5. Handle Errors Gracefully
   If a column doesn't exist, check available columns first using get_columns.
   Provide helpful error messages and suggest corrections.
   If data isn't loaded, guide the user to load it first.

6. Communication Style
   Be clear and concise in your explanations.
   Use proper statistical terminology but explain it when necessary.
   Structure your responses logically (overview → specific findings → conclusions).
   Ask clarifying questions when the user's request is ambiguous.

**VERY IMPORTANT: Output Format**
When you need to use a tool, you MUST respond in the following format:
Action: [the name of the tool to use, e.g., load_csv]
Action Input: [the input to the tool]

After the tool has been executed, you will receive an Observation. You will then think about the next step.
If you have gathered enough information to answer the user's question, you MUST provide the final answer in the following format:
Final Answer: [your comprehensive answer to the user's original question based on the tool outputs]

DO NOT output any other text after "Final Answer:". Your entire response should be just that line if you are providing the final answer.

Example Response Pattern
When analyzing data, follow this structure:
Data Loading: Confirm the dataset is loaded (internally, using tools).
Data Overview: Provide basic information about columns and structure (internally, using tools).
Specific Analysis: Perform the requested calculations (internally, using tools).
Final Output: Present the findings prefixed with "Final Answer:".

Important Notes
- Always verify data is loaded before attempting analysis.
- Column names are case-sensitive - use exact matches.
- Provide statistical context (e.g., what constitutes high/low variability).
- If asked about columns that don't exist, list available columns to help the user.
- Remember that you're working with a single DataFrame stored in memory.

Your goal is to make data analysis accessible and insightful, helping users understand their data through clear explanations and methodical analysis, strictly adhering to the specified output format.
"""


def Dataframe_agent(file_path,prompt,api):
    df_store={}

    llm,embedding=Gemini_llm_embedding(api)


    @tool
    def load_csv(csv_path:str)->str:
        '''Load a csv file and save it as a dataframe'''
        csv_path=csv_path.replace("_", " ")
        try:
            df=pd.read_csv(csv_path)
            df_store["df"]=df
            return f"File loaded successfully as a dataframe with {len(df)} rows and {len(df.columns)} columns"
        except Exception as e:
            return f"Error loading file: {str(e)}"
    
    @tool
    def count_elem(col: str) -> str:
        '''Counts each time an element appears in a column'''
        try:
            if "df" not in df_store:
                return "Error: No dataframe loaded. Please load a CSV file first."
            if col not in df_store['df'].columns:
                available_cols = df_store['df'].columns.tolist()
                return f"Error: Column '{col}' not found. Available columns: {available_cols}"
            
            counts = df_store['df'][col].value_counts().to_dict()
            return f"Value counts for column '{col}': {counts}"
        except Exception as e:
            return f"Error counting elements: {str(e)}"

    @tool
    def most_pop_elem(col:str)->str:
        '''Returns the most frequent value of a column'''
        try:
            if "df" not in df_store:
                return "Error: No dataframe loaded. Please load a CSV file first."
            if col not in df_store['df'].columns:
                available_cols = df_store['df'].columns.tolist()
                return f"Error: Column '{col}' not found. Available columns: {available_cols}"
            
            # Get the most frequent value using value_counts
            most_frequent = df_store['df'][col].value_counts().index[0]
            frequency = df_store['df'][col].value_counts().iloc[0]
            
            return f"Most popular element in column '{col}': '{most_frequent}' (appears {frequency} times)"
        except Exception as e:
            return f"Error finding most popular element: {str(e)}"

    @tool
    def get_columns(dummy:str)->str:
        '''Returns the columns of a dataframe'''
        try:
            if "df" not in df_store:
                return "Error: No dataframe loaded. Please load a CSV file first."
            columns=df_store['df'].columns.tolist()
            return f"Available columns: {columns}"
        except Exception as e:
            return f"Error getting columns: {str(e)}"

    @tool
    def describe_csv(dummy:str)->str:
        '''Returns descriptive statistics for the dataframe'''
        try:
            if "df" not in df_store:
                return "Error: No dataframe loaded. Please load a CSV file first."
            description=df_store['df'].describe()
            return f"Descriptive statistics:\n{description.to_string()}"
        except Exception as e:
            return f"Error describing dataframe: {str(e)}"

    @tool
    def average_col(col:str)->str:
        '''Returns the average value of a column'''
        try:
            if "df" not in df_store:
                return "Error: No dataframe loaded. Please load a CSV file first."
            if col not in df_store['df'].columns:
                available_cols = df_store['df'].columns.tolist()
                return f"Error: Column '{col}' not found. Available columns: {available_cols}"
            
            # Check if column is numeric
            if not pd.api.types.is_numeric_dtype(df_store['df'][col]):
                return f"Error: Column '{col}' is not numeric. Cannot calculate average."
            
            avg=df_store['df'][col].mean()
            return f"Average of column '{col}': {avg}"
        except Exception as e:
            return f"Error calculating average: {str(e)}"

    @tool
    def st_dev_col(col:str)->str:
        '''Returns the standard deviation of a column'''
        try:
            if "df" not in df_store:
                return "Error: No dataframe loaded. Please load a CSV file first."
            if col not in df_store['df'].columns:
                available_cols = df_store['df'].columns.tolist()
                return f"Error: Column '{col}' not found. Available columns: {available_cols}"
            
            # Check if column is numeric
            if not pd.api.types.is_numeric_dtype(df_store['df'][col]):
                return f"Error: Column '{col}' is not numeric. Cannot calculate standard deviation."
            
            std=df_store['df'][col].std()
            return f"Standard deviation of column '{col}': {std}"
        except Exception as e:
            return f"Error calculating standard deviation: {str(e)}"

    tools=[st_dev_col,average_col,describe_csv,get_columns,load_csv,count_elem,most_pop_elem]

    agent=initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=False,
        handle_parsing_error=True
    )
    full_prompt=f"{csv_system_prompt}\nThe user has asked: {prompt}\nThe designed file is {file_path}."
    return agent.run(full_prompt)

class PdfPrompt:
    def __init__(self,prompt,vector_store,llm):
        self.prompt=prompt
        self.vector_store=vector_store
        self.llm=llm
    
    def retrieve_docs(self):
        docs=self.vector_store.similarity_search(self.prompt,k=10,filter={'source':'pdf'})
        return docs
    
    def agent_prompt(self):
        docs=self.retrieve_docs()
        context=""
        for doc in docs:
            context+=f'{doc}'

        new_prompt=f"You are an assistant for question-answering tasks in a dairy company called Case-Aria s.r.l. Use the following pieces of retrieved context to answer the question. Keep the answer concise. Question: {self.prompt}\nContext: {context}\nAnswer:\n"

        return new_prompt
