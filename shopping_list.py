import pandas as pd
import streamlit as st


from google_sheet import get_orders, update_status, update_amount


def existing_list():
    shopping_list = get_orders()
    # Make amount values into int
    shopping_list = [
        [*order[:3], int(order[3]) if order[3] != '' else None, *order[4:]]
        for order in shopping_list
    ]
    # Make status false
    shopping_list = [[*order[:4], False, *order[5:]] for order in shopping_list]
    df = pd.DataFrame(shopping_list, columns=['ID', 'Date', 'Product', 'Amount', 'Status', 'Ordered by'])

    new_data = st.data_editor(
                    df,
                    hide_index=True,
                    column_config={
                        # 'ID': None,
                        'Date': None,
                        # 'Status': None,
                        'Ordered by': None,
                        # 'Ordered by': st.column_config.SelectboxColumn(
                        #     options=['Dad', 'Mom', 'Alex', 'Leanne', 'Yoel']
                        # ),
                        'Amount': st.column_config.NumberColumn(),
                        'Status': st.column_config.CheckboxColumn(
                            label='Check off',
                            default=False
                        )
                    },
                )

    return new_data


def update_list(new_data):
    for row in new_data.itertuples(index=False):
        if row.Status is True:
            update_status(row.ID)
        if pd.notna(row.Amount):
            update_amount(row.ID, row.Amount)
    st.rerun()

