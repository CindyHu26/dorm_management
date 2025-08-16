import streamlit as st
import pandas as pd
from datetime import datetime
from data_models import lease_model, dormitory_model

def render():
    """渲染「合約管理」頁面"""
    st.header("租賃合約管理")

    if 'selected_lease_id' not in st.session_state:
        st.session_state.selected_lease_id = None

    # --- 1. 新增合約 ---
    with st.expander("➕ 新增租賃合約"):
        with st.form("new_lease_form", clear_on_submit=True):
            dorms = dormitory_model.get_dorms_for_selection() or []
            dorm_options = {d['id']: d['original_address'] for d in dorms}
            
            selected_dorm_id = st.selectbox("選擇宿舍地址", options=dorm_options.keys(), format_func=lambda x: dorm_options[x])
            
            c1, c2 = st.columns(2)
            lease_start_date = c1.date_input("合約起始日", value=None)
            lease_end_date = c2.date_input("合約截止日", value=None)
            
            c3, c4, c5 = st.columns(3)
            monthly_rent = c3.number_input("月租金", min_value=0, step=1000)
            deposit = c4.number_input("押金", min_value=0, step=1000)
            utilities_included = c5.checkbox("租金含水電")

            submitted = st.form_submit_button("儲存新合約")
            if submitted:
                details = {
                    "dorm_id": selected_dorm_id,
                    "lease_start_date": str(lease_start_date) if lease_start_date else None,
                    "lease_end_date": str(lease_end_date) if lease_end_date else None,
                    "monthly_rent": monthly_rent,
                    "deposit": deposit,
                    "utilities_included": utilities_included
                }
                success, message, _ = lease_model.add_lease(details)
                if success:
                    st.success(message)
                    st.cache_data.clear()
                else:
                    st.error(message)

    st.markdown("---")

    # --- 2. 合約總覽與篩選 ---
    st.subheader("現有合約總覽")
    
    dorm_filter_options = {0: "所有宿舍"} | {d['id']: d['original_address'] for d in dorms}
    dorm_id_filter = st.selectbox("篩選宿舍", options=dorm_filter_options.keys(), format_func=lambda x: dorm_filter_options[x])

    @st.cache_data
    def get_leases(filter_id):
        return lease_model.get_leases_for_view(filter_id if filter_id else None)

    leases_df = get_leases(dorm_id_filter)
    
    selection = st.dataframe(leases_df, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key="lease_selector")
    
    if selection['rows']:
        st.session_state.selected_lease_id = int(leases_df.iloc[selection['rows'][0]]['id'])

    st.markdown("---")

    # --- 3. 單一合約詳情與編輯 ---
    if st.session_state.selected_lease_id:
        lease_details = lease_model.get_single_lease_details(st.session_state.selected_lease_id)
        if not lease_details:
            st.error("找不到選定的合約資料。")
            st.session_state.selected_lease_id = None
        else:
            st.subheader(f"編輯合約 (ID: {lease_details['id']})")
            with st.form("edit_lease_form"):
                st.text_input("宿舍地址", value=dorm_options.get(lease_details['dorm_id'], "未知"), disabled=True)
                
                ec1, ec2 = st.columns(2)
                start_date_val = datetime.strptime(lease_details['lease_start_date'], '%Y-%m-%d').date() if lease_details.get('lease_start_date') else None
                end_date_val = datetime.strptime(lease_details['lease_end_date'], '%Y-%m-%d').date() if lease_details.get('lease_end_date') else None
                
                e_lease_start_date = ec1.date_input("合約起始日", value=start_date_val)
                e_lease_end_date = ec2.date_input("合約截止日", value=end_date_val)
                
                ec3, ec4, ec5 = st.columns(3)
                e_monthly_rent = ec3.number_input("月租金", min_value=0, step=1000, value=lease_details.get('monthly_rent', 0))
                e_deposit = ec4.number_input("押金", min_value=0, step=1000, value=lease_details.get('deposit', 0))
                e_utilities_included = ec5.checkbox("租金含水電", value=bool(lease_details.get('utilities_included', False)))

                edit_submitted = st.form_submit_button("儲存變更")
                if edit_submitted:
                    updated_details = {
                        "lease_start_date": str(e_lease_start_date) if e_lease_start_date else None,
                        "lease_end_date": str(e_lease_end_date) if e_lease_end_date else None,
                        "monthly_rent": e_monthly_rent,
                        "deposit": e_deposit,
                        "utilities_included": e_utilities_included
                    }
                    success, message = lease_model.update_lease(st.session_state.selected_lease_id, updated_details)
                    if success:
                        st.success(message)
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(message)

            confirm_delete = st.checkbox("我了解並確認要刪除此筆合約")
            if st.button("🗑️ 刪除此合約", type="primary", disabled=not confirm_delete):
                success, message = lease_model.delete_lease(st.session_state.selected_lease_id)
                if success:
                    st.success(message)
                    st.session_state.selected_lease_id = None
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(message)