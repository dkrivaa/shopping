import time

import streamlit as st
import speech_recognition as sr
from pydantic_ai import Agent
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import asyncio

from google_sheet import add_order
from shopping_list import existing_list, update_list


st.set_page_config(
    page_title="My App",
    page_icon="grocery_9564896.png"  # Ensure this is in the app folder
)


# Load env variables
load_dotenv()
groq_api_key = os.getenv('GROQ_API_KEY')


class Order(BaseModel):
    product: str | None
    amount: int | None


# Define agent
transcript_agent = Agent(
    model='groq:llama-3.3-70b-versatile',
    result_type=Order,
    system_prompt="""
        You are an excellent grocery shopping list writer assistant.
        When provided with two possibilities for items to add to a shopping list, you will
        return the most appropriate of the two.

        If neither of the possibilities seem appropriate for a grocery shopping list, return 
        product as empty string.

        If the returned item includes an amount, you will split the item into product and amount.
        There should be no amount in the product string.
        If the returned item does not include an amount, leave the amount as None.
        You do not have to translate from hebrew to english but if the item is in hebrew it should
        adhere to the rules mentioned above with regard to no amount in product.

        Whether in english or in hebrew, the product should not include an amount!

    """
)

# Ensure an event loop is available
try:
    asyncio.get_running_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())


# Add order to the shopping list
def accept_order(product, amount):
    add_order([product, amount])


@st.dialog('Your order:')
def approve(product, amount):
    st.write('product:', product)


def update_session_state(choice):
    if choice != st.session_state.choice:
        st.session_state.choice = choice


# Dialog to choose manually if no access to AI to run agent
@st.dialog('Choose your order:')
def manual_approve(text_en, text_he):

    new_choice = st.radio(label='We need your help:', options=[text_en, text_he], index=None,
                          key='choice')

    # If user makes choice
    if new_choice:
        st.write(st.session_state.choice)
        add_order([st.session_state.choice, None])
        del st.session_state.choice
        st.rerun()


def manual_process():
    text_en = st.session_state.options['text_en']
    text_he = st.session_state.options['text_he']

    manual_approve(text_en, text_he)
    # if 'choice' in st.session_state.choice:
    #     add_order([st.session_state.choice, None])


# Make english and hebrew transcript to feed to agent
def transcript(message):
    # Speech recognition
    recognizer = sr.Recognizer()
    with sr.AudioFile(message) as source:
        audio_data = recognizer.record(source)

        try:
            text_en = recognizer.recognize_google(audio_data, language="en-US")
            text_he = recognizer.recognize_google(audio_data, language="he-IL")
            return text_en, text_he
        except sr.UnknownValueError:
            st.error("Could not understand the audio.")
        except sr.RequestError:
            st.error("Could not request results, please check your internet connection.")


def transcript_order(message):
    try:
        text_en, text_he = transcript(message)

        # Try if there is access to groq to run agent
        try:
            # Run transcript agent
            item_to_add = transcript_agent.run_sync(user_prompt=f'please return appropriate item: '
                                                                f'{text_en} or '
                                                                f'{text_he}')
            # If agent came to decision
            if item_to_add.data != '':
                result = item_to_add.data
                # Make dict from agent RunResult
                result_dict = result.model_dump()
                product = result_dict['product']
                amount = result_dict['amount']

                if product != '':
                    return [product, amount]
                else:
                    return "Could not understand your order. Please try again."

            # If agent could not make a decision
            else:
                return "Could not understand your order. Please try again."

        except:
            # Run alternative manual process
            if 'options' not in st.session_state:
                st.session_state.options = {'text_en': text_en, 'text_he': text_he}
            else:
                st.session_state.options = {'text_en': text_en, 'text_he': text_he}
            return 'manual'


    except TypeError:
        pass


@st.fragment
def updated_list():
    st.subheader('Existing Orders')
    new_data = existing_list()

    if st.button('Update list', key='update_button'):
        update_list(new_data)


def main():
    if 'choice' not in st.session_state:
        st.session_state.choice = None
    st.subheader('Family Shopping List')
    with st.form('new_order', clear_on_submit=True):
        message = st.audio_input('**Enter order**')

        # Submit button
        submitted = st.form_submit_button('Submit')
        if submitted:
            if message:
                result = transcript_order(message)
                if isinstance(result, list):
                    product = result[0]
                    amount = result[1]
                    if product != '':
                        add_order([product, amount])
                    else:
                        st.error(result)
                elif result == 'manual':
                    manual_process()
                else:
                    st.error(result)
            else:
                st.error('You did not enter any order.')

    st.divider()
    # Update shopping list for changes made by user
    updated_list()


if __name__ == "__main__":
    main()




