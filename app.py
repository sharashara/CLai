import chainlit as cl
from chainlit.input_widget import Select
import vanna
from vanna.remote import VannaDefault
from typing import Optional
import os

vanna_api_key = os.environ["VANNA_API_KEY"]
vanna_model = os.environ["VANNA_MODEL"]
vn = VannaDefault(model=vanna_model, api_key=vanna_api_key)

bigquery_project_id = os.environ["BIGQUERY_PROJECT_ID"]
cred_file_path = os.environ["BIGQUERY_CRED_FILE_PATH"]
bigquery_cred_file = os.environ["BIGQUERY_CRED_FILE"]
with open(cred_file_path, "w") as f:
    f.write(bigquery_cred_file)
vn.connect_to_bigquery(project_id=bigquery_project_id, cred_file_path=cred_file_path)

admin_username = os.environ["ADMIN_USERNAME"]
admin_password = os.environ["ADMIN_PASSWORD"]
@cl.password_auth_callback
def auth_callback(username: str, password: str):
    if (username, password) == (admin_username, admin_password):
        return cl.User(
            identifier="admin", metadata={"role": "admin", "provider": "credentials"}
        )
    else:
        return None

@cl.step(root=True, language="sql", name="CL.ai")
async def gen_query(human_query: str):
    sql_query = vn.generate_sql(human_query)
    return sql_query

@cl.step(root=True, name="CL.ai")
async def execute_query(query):
    current_step = cl.context.current_step
    df = vn.run_sql(query)
    current_step.output = df.head().to_markdown(index=False)

    return df

@cl.step(name="Plot", language="python")
async def plot(human_query, sql, df):
    current_step = cl.context.current_step
    plotly_code = vn.generate_plotly_code(question=human_query, sql=sql, df=df)
    fig = vn.get_plotly_figure(plotly_code=plotly_code, df=df)

    current_step.output = plotly_code
    return fig

@cl.step(type="run", root=True, name="CL.ai")
async def chain(human_query: str):
    sql_query = await gen_query(human_query)
    df = await execute_query(sql_query)    
    fig = await plot(human_query, sql_query, df)

    elements = [cl.Plotly(name="chart", figure=fig, display="inline")]
    await cl.Message(content=human_query, elements=elements, author="CL.ai").send()

@cl.on_message
async def main(message: cl.Message):
    await chain(message.content)

@cl.on_chat_start
async def setup():
    await cl.Avatar(
        name="CL.ai",
        # url="https://chinlai.com.my/wp-content/uploads/2021/11/cllogo.png",
        url="https://scontent.fkul21-2.fna.fbcdn.net/v/t39.30808-6/300450858_543806034209851_8062497851724931535_n.png?_nc_cat=106&ccb=1-7&_nc_sid=5f2048&_nc_ohc=IQe4RKsx1k4Q7kNvgGl9Wjz&_nc_ht=scontent.fkul21-2.fna&oh=00_AfAjyhuuVjn2ogclWtl4nE9XWuXIkxUzgNqidBBmhFCXZg&oe=6638F927",
    ).send()

    # settings = await cl.ChatSettings(
    #     [
    #         Select(
    #             id="Model",
    #             label="OpenAI - Model",
    #             values=["gpt-4-turbo", "gpt-3.5-turbo-16k","gpt-3.5-turbo",],
    #             initial_index=0,
    #         )
    #     ]
    # ).send()
    # value = settings["Model"]