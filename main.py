import streamlit as st
from services.auth.login_wall import render_login_wall
from services.state.sessions_defaults import initial_session_defaults
from services.config.workout_config import EXCERCISE_OPTIONS

def main():
    st.set_page_config(
        page_icon = "🏋️‍♂️",
        page_title = "AI Real-Time Gym Trainer",
        layout = "centered",
        initial_sidebar_state = "expanded"
    )
    if not render_login_wall():
        return
    
    initial_session_defaults()
    
    workout_started = st.session_state.get("Workout_Started", False)
    
    with st.sidebar:
        st.title("🏋️‍♂️ Apna AI Coach")
        
        if st.session_state.username:
            st.caption(f" Login as {st.session_state.username}")
            
        st.divider()
        
        st.subheader("Workout Plan")
        if not workout_started:
            st.selectbox("Excercise", options= EXCERCISE_OPTIONS, key="plan_exercise")
            
            st.number_input("Sets", min_value = 0, max_value = 50, key = "plan_sets", step = 1)
            
            st.number_input("Reps per Set", min_value = 0, max_value = 50, key = "plan_reps", step = 1)
            
            st.markdown("")
            
            start_session_button = st.button("Start Session", width = "stretch", key = "start_session_button")
            
            if start_session_button:
                st.session_state["Workout_Started"] = True
                st.rerun()
            else:
                excercise = st.session_state.get("plan_excercise")
                sets = st.session_state.get("plan_sets")
                reps = st.session_state.get("plan_reps")
                
                st.info(f"**{excercise}** -- {sets} Sets / {reps} Reps")
                
                end_session_button = st.button("End Session", key = "end_session_button", width = "stretch")
                
                if end_session_button:
                    st.session_state["workout_started"] = False
    
    if workout_started:
        st.divider()
        
        excercise = st.session_state.get("plan_excercise")
        total_reps = st.session_state.get("reps")
        current_set_reps = st.session_state.get("current_set_reps")
        reps_per_set = st.session_state.get("plan_reps")
        sets_completed = st.session_state.get("sets_completed")
        target_sets = st.session_state.get("plan_sets")
        
        st.subheader("Progress")
        
        st.metrics("Total Reps", f"{total_reps}" )
        st.metrics("Current Set Reps", f"{current_set_reps}/{reps_per_set}")
        st.metrics("Sets Completed", f"{sets_completed}/{target_sets}")
    
    

    if __name__ == "__main__":
        main()