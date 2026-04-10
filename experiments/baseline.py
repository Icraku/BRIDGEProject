from pathlib import Path
from typing import List,Any
from PIL import Image
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel
from langchain.chains.base import Chain

from schemas import a_infant_details

from pdftoImage.pdftoimgPage1 import pdf_to_png

# Step 1: Gets the pdf path and returns the list of images in the pdf2img_utils file, then it is called here
def pdf2image(path:Path)->List[Image]:
    """
    Wrapper around pdf_utils that calls the converter and returns a list of PIL Images.
    """
    images = pdf_to_png(path)
    return images

# Step 2: Simple preprocessing that will come on later in the project
def simple_preprocess(images:List[Image])->List[Image]:
    """
    Placeholder function that just returns the list of PIL Images.
    :param images: List of PIL Images.
    :return: images
    """
    return images
# pdf2image -> preprocessing -> model-> Pydantic


baseline_template = ChatPromptTemplate()


def get_model(model_name:str,
              prompt_template: ChatPromptTemplate,
              schema: type[BaseModel]
              )->Chain:
    llm = ChatOpenAI(model=model_name, temperature=0)
    structured_llm = llm.with_structured_output(schema)

    prompt = ChatPromptTemplate.from_messages([
        ("human", "What's the weather like in {location}?")
    ])
    chain = prompt | structured_llm
    return chain


if __name__ == "__main__":
    """
    pdf2 = ""
    list_img2=pdf2image(pdf2)
    """

    pdf_input = input("Enter the path or URL of the PDF file: ").strip()

    # Step 1 — Convert to images
    list_img1 = pdf2image(pdf_input)
    print(list_img1)
    print(f"\n Converted {len(list_img1)} pages.")
    for i, img in enumerate(list_img1):
        print(f"Page {i + 1}: mode={img.mode}, size={img.size}")

    """
    proprocessed_img1 = simple_preprocess(list_img1)
    model=get_model("gemma",baseline_template,schema=nar.InfantDetails)
    result=model.invoke(proprocessed_img1)
    """

