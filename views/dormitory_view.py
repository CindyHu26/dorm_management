import streamlit as st
import pandas as pd
from datetime import datetime
from data_models import dormitory_model 
from data_processor import normalize_taiwan_address

def render():
    """渲染「地址管理」頁面的所有 Streamlit UI 元件。"""
    st.header("宿舍地址管理")

    if 'selected_dorm_id' not in st.session_state:
        st.session_state.selected_dorm_id = None

    # --- 1. 新增宿舍區塊 ---
    with st.expander("➕ 新增宿舍地址", expanded=False):
        with st.form("new_dorm_form", clear_on_submit=True):
            st.subheader("宿舍基本資料")
            c1, c2 = st.columns(2)
            legacy_code = c1.text_input("舊系統編號 (選填)")
            original_address = c1.text_input("原始地址 (必填)")
            dorm_name = c2.text_input("宿舍自訂名稱 (例如: 中山A棟)")
            
            st.subheader("責任歸屬")
            rc1, rc2, rc3 = st.columns(3)
            primary_manager = rc1.selectbox("主要管理人", ["我司", "雇主"], key="new_pm")
            rent_payer = rc2.selectbox("租金支付方", ["我司", "雇主", "工人"], key="new_rp")
            utilities_payer = rc3.selectbox("水電支付方", ["我司", "雇主", "工人"], key="new_up")
            management_notes = st.text_area("管理模式備註 (可記錄特殊約定)")
            
            norm_addr_preview = normalize_taiwan_address(original_address)['full'] if original_address else ""
            if norm_addr_preview: st.info(f"正規化地址預覽: {norm_addr_preview}")

            submitted = st.form_submit_button("儲存新宿舍")
            if submitted:
                if not original_address:
                    st.error("「原始地址」為必填欄位！")
                else:
                    dorm_details = {
                        'legacy_dorm_code': legacy_code, 'original_address': original_address,
                        'normalized_address': norm_addr_preview, 'dorm_name': dorm_name,
                        'primary_manager': primary_manager, # 將新欄位加入儲存
                        'rent_payer': rent_payer, 'utilities_payer': utilities_payer,
                        'management_notes': management_notes
                    }
                    success, message = dormitory_model.add_new_dormitory(dorm_details)
                    if success:
                        st.success(message)
                        st.cache_data.clear()
                    else:
                        st.error(message)

    st.markdown("---")

    # --- 2. 宿舍總覽與篩選 ---
    st.subheader("現有宿舍總覽")
    
    @st.cache_data
    def get_dorms_df():
        return dormitory_model.get_all_dorms_for_view()

    dorms_df = get_dorms_df()

    search_term = st.text_input("搜尋宿舍 (可輸入舊編號、名稱或地址關鍵字)")
    if search_term and not dorms_df.empty:
        search_mask = dorms_df.apply(lambda row: row.astype(str).str.contains(search_term, case=False, na=False).any(), axis=1)
        dorms_df = dorms_df[search_mask]
    
    selection = st.dataframe(dorms_df, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")

    if selection.selection['rows']:
        st.session_state.selected_dorm_id = int(dorms_df.iloc[selection.selection['rows'][0]]['id'])
    
    st.markdown("---")
    
    # --- 3. 單一宿舍詳情與管理 ---
    if st.session_state.selected_dorm_id:
        dorm_id = st.session_state.selected_dorm_id
        dorm_details = dormitory_model.get_dorm_details_by_id(dorm_id)
        
        if not dorm_details:
            st.error("找不到選定的宿舍資料，可能已被刪除。請重新整理。")
            st.session_state.selected_dorm_id = None
        else:
            st.subheader(f"詳細資料: {dorm_details.get('original_address', '')}")
            
            tab1, tab2 = st.tabs(["基本資料與編輯", "房間管理"])

            with tab1:
                with st.form("edit_dorm_form"):
                    st.markdown("##### 基本資料")
                    edit_c1, edit_c2 = st.columns(2)
                    legacy_code = edit_c1.text_input("舊系統編號", value=dorm_details.get('legacy_dorm_code', ''))
                    original_address = edit_c1.text_input("原始地址", value=dorm_details.get('original_address', ''))
                    dorm_name = edit_c2.text_input("宿舍自訂名稱", value=dorm_details.get('dorm_name', ''))
                    
                    st.markdown("##### 責任歸屬")
                    edit_rc1, edit_rc2, edit_rc3 = st.columns(3)
                    manager_options = ["我司", "雇主", "工人"]
                    primary_manager = edit_rc1.selectbox("主要管理人", manager_options, index=manager_options.index(dorm_details.get('primary_manager')) if dorm_details.get('primary_manager') in manager_options else 0)
                    rent_payer = edit_rc2.selectbox("租金支付方", manager_options, index=manager_options.index(dorm_details.get('rent_payer')) if dorm_details.get('rent_payer') in manager_options else 0)
                    utilities_payer = edit_rc3.selectbox("水電支付方", manager_options, index=manager_options.index(dorm_details.get('utilities_payer')) if dorm_details.get('utilities_payer') in manager_options else 0)
                    
                    management_notes = st.text_area("管理模式備註", value=dorm_details.get('management_notes', ''))
                    
                    edit_submitted = st.form_submit_button("儲存變更")
                    if edit_submitted:
                        updated_details = {
                            'legacy_dorm_code': legacy_code, 'original_address': original_address,
                            'dorm_name': dorm_name, 'primary_manager': primary_manager,
                            'rent_payer': rent_payer, 'utilities_payer': utilities_payer,
                            'management_notes': management_notes
                        }
                        success, message = dormitory_model.update_dormitory_details(dorm_id, updated_details)
                        if success:
                            st.success(message)
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(message)

                st.markdown("---")
                st.markdown("##### 危險操作區")
                confirm_delete = st.checkbox("我了解並確認要刪除此宿舍")
                if st.button("🗑️ 刪除此宿舍", type="primary", disabled=not confirm_delete):
                    success, message = dormitory_model.delete_dormitory_by_id(dorm_id)
                    if success:
                        st.success(message)
                        st.session_state.selected_dorm_id = None
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(message)

            with tab2:
                st.markdown("##### 房間列表")
                rooms_df = dormitory_model.get_rooms_for_dorm_as_df(dorm_id)
                st.dataframe(rooms_df, use_container_width=True, hide_index=True)

                c1, c2 = st.columns([3,1])
                with c1:
                    with st.form("new_room_form", clear_on_submit=True):
                        st.markdown("###### 新增房間至此宿舍")
                        rc1, rc2, rc3 = st.columns(3)
                        room_number = rc1.text_input("房號")
                        capacity = rc2.number_input("房間容量", min_value=0, step=1)
                        gender_policy = rc3.selectbox("性別限制", ["可混住", "僅限男性", "僅限女性"])
                        if st.form_submit_button("新增房間"):
                            if not room_number:
                                st.error("房號為必填欄位！")
                            else:
                                room_details = {'dorm_id': dorm_id, 'room_number': room_number, 'capacity': capacity, 'gender_policy': gender_policy}
                                success, msg, _ = dormitory_model.add_new_room_to_dorm(room_details)
                                if success:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
                with c2:
                    with st.form("delete_room_form", clear_on_submit=True):
                        st.markdown("###### 刪除房間")
                        room_to_delete = st.selectbox("選擇要刪除的房間", options=[""] + rooms_df['room_number'].tolist())
                        if st.form_submit_button("刪除選定房間", type="primary"):
                            if not room_to_delete:
                                st.warning("請選擇一個房間。")
                            else:
                                room_id_to_delete = rooms_df[rooms_df['room_number'] == room_to_delete].iloc[0]['id']
                                success, message = dormitory_model.delete_room_by_id(room_id_to_delete)
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)