ef get_gemini_response(question, prompt):
    model = genai.GenerativeModel('gemini-pro')
    response = model.gene