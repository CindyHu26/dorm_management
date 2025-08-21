import streamlit as st
from data_models import maintenance_model

def render():
    """渲染「系統維護」頁面"""
    st.header("系統維護工具")

    st.markdown("---")

    # --- 日期格式校正工具 ---
    with st.container(border=True):
        st.subheader("資料庫日期格式一鍵校正")
        st.warning("警告：這是一個高階維護工具，它將會修改資料庫中所有表格的日期格式。請在遇到儀表板數據異常（例如人數為0）時，才謹慎使用。")
        st.info("執行此工具前，強烈建議複製'dorm_management.db'備份您的資料庫。")

        if st.button("🚀 開始執行日期格式校正", type="primary"):
            with st.spinner("正在全面掃描並校正資料庫日期格式，請稍候..."):
                report = maintenance_model.fix_all_date_formats()
            
            st.success("校正程序執行完畢！")
            
            st.subheader("執行報告:")
            # 使用 st.code 來顯示多行報告，格式更清晰
            st.code("\n".join(report))

            # 清除所有快取，確保下次載入時能讀到最新的、已校正的資料
            st.cache_data.clear()
            st.info("所有應用程式快取已清除，請重新整理頁面或切換到其他頁面以查看最新數據。")