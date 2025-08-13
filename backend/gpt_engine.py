import os
import re
from openai import OpenAI
from dotenv import load_dotenv

class GPTEngine:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv('OPENAI_API_KEY')
        self.client = OpenAI(api_key=api_key)

    def generate_response(self, question, resume_text=None, mode="global", history=None):
        if not question.strip():
            return "No question provided."
        
        import sys
        print(f"[DEBUG] generate_response called with mode={mode}, resume_text_len={len(resume_text) if resume_text else 0}")
        sys.stdout.flush()
        
        is_intro = self._is_intro_question(question)
        
        if mode == "resume" and resume_text and resume_text.strip():
            # Smart mode: Use resume context if possible, else give a general answer for the question (not a template)
            if is_intro:
                system_prompt = (
                    "You are an interview assistant. Write a first-person introduction using ONLY the facts found in the resume below. "
                    "If the resume does not contain enough information, answer the question directly in the user's point of view (first-person), with a practical, specific answer. Do NOT use a template, structure, generic example, fallback message, or any instructional text.\n\nResume:\n" + resume_text
                )
            else:
                system_prompt = (
                    "You are an interview assistant. Answer ONLY using the resume below. If the resume does not cover the question, answer the question directly in the user's point of view (first-person), with a concise, practical, specific answer. Do NOT use a template, structure, generic example, fallback message, or any instructional text.\n\nResume:\n" + resume_text
                )
            print("[DEBUG] SMART MODE PROMPT SENT TO OPENAI:\n", system_prompt[:1000])
            sys.stdout.flush()
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            if history and isinstance(history, list) and len(history) > 0:
                messages += history
            messages.append({"role": "user", "content": question})
        else:
            # Global mode: answer purely general questions
            system_prompt = (
                "You are a helpful interview assistant. Provide general interview advice, tips, and guidance. "
                "Focus on common interview questions, best practices, and general career advice. "
                "Do not reference any specific resume or personal information unless provided in the conversation."
            )
            print(f"[DEBUG] GLOBAL MODE PROMPT SENT TO OPENAI:\n{system_prompt}")
            sys.stdout.flush()
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            if history and isinstance(history, list) and len(history) > 0:
                messages += history
            messages.append({"role": "user", "content": question})
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=512,
                temperature=(0.5 if (mode == "resume" and is_intro) else (0.45 if mode == "resume" else 0.7)),
            )
            answer = response.choices[0].message.content.strip()
            # --- STRICT SMART MODE FILTER ---
            if mode == "resume" and resume_text and resume_text.strip():
                # Remove any answer that looks like a template, fallback, or instructional text
                forbidden_phrases = [
                    "As an AI language model",
                    "As an interview assistant",
                    "I'm sorry",
                    "I am unable to",
                    "I cannot answer",
                    "Based on the information provided",
                    "Based on your resume",
                    "Here is a sample answer",
                    "Here is a template",
                    "Here is an example",
                    "Here is a possible answer",
                    "Here is a general answer",
                    "Here is a suggested answer",
                    "Here is a response",
                    "Here is a possible response",
                    "Here is a template response",
                    "Here is a sample response",
                    "Here is a generic answer",
                    "Here is a generic response",
                    "Here is a fallback answer",
                    "Here is a fallback response",
                    "Here is an instructional text",
                    "Here is an instructional response",
                    "Here is a structured answer",
                    "Here is a structured response",
                    "Here is a structured template",
                    "Here is a structured example",
                    "Here is a structured sample",
                    "Here is a structured suggestion",
                    "Here is a structured guidance",
                    "Here is a structured tip",
                    "Here is a structured advice",
                    "Here is a structured best practice",
                    "Here is a structured career advice",
                    "Here is a structured interview advice",
                    "Here is a structured interview tip",
                    "Here is a structured interview guidance",
                    "Here is a structured interview best practice",
                    "Here is a structured interview answer",
                    "Here is a structured interview response",
                    "Here is a structured interview template",
                    "Here is a structured interview example",
                    "Here is a structured interview sample",
                    "Here is a structured interview suggestion",
                    "Here is a structured interview guidance",
                    "Here is a structured interview tip",
                    "Here is a structured interview advice",
                    "Here is a structured interview best practice",
                    "Here is a structured interview answer",
                    "Here is a structured interview response",
                    "Here is a structured interview template",
                    "Here is a structured interview example",
                    "Here is a structured interview sample",
                    "Here is a structured interview suggestion",
                    "Here is a structured interview guidance",
                    "Here is a structured interview tip",
                    "Here is a structured interview advice",
                    "Here is a structured interview best practice",
                    "Here is a structured interview answer",
                    "Here is a structured interview response",
                    "Here is a structured interview template",
                    "Here is a structured interview example",
                    "Here is a structured interview sample",
                    "Here is a structured interview suggestion",
                    "Here is a structured interview guidance",
                    "Here is a structured interview tip",
                    "Here is a structured interview advice",
                    "Here is a structured interview best practice",
                    "Here is a structured interview answer",
                    "Here is a structured interview response",
                    "Here is a structured interview template",
                    "Here is a structured interview example",
                    "Here is a structured interview sample",
                    "Here is a structured interview suggestion",
                    "Here is a structured interview guidance",
                    "Here is a structured interview tip",
                    "Here is a structured interview advice",
                    "Here is a structured interview best practice",
                    "Here is a structured interview answer",
                    "Here is a structured interview response",
                    "Here is a structured interview template",
                    "Here is a structured interview example",
                    "Here is a structured interview sample",
                    "Here is a structured interview suggestion",
                    "Here is a structured interview guidance",
                    "Here is a structured interview tip",
                    "Here is a structured interview advice",
                    "Here is a structured interview best practice",
                    "Here is a structured interview answer",
                    "Here is a structured interview response",
                    "Here is a structured interview template",
                    "Here is a structured interview example",
                    "Here is a structured interview sample",
                    "Here is a structured interview suggestion",
                    "Here is a structured interview guidance",
                    "Here is a structured interview tip",
                    "Here is a structured interview advice",
                    "Here is a structured interview best practice",
                    "Here is a structured interview answer",
                    "Here is a structured interview response",
                    "Here is a structured interview template",
                    "Here is a structured interview example",
                    "Here is a structured interview sample",
                    "Here is a structured interview suggestion",
                    "Here is a structured interview guidance",
                    "Here is a structured interview tip",
                    "Here is a structured interview advice",
                    "Here is a structured interview best practice",
                    "Here is a structured interview answer",
                    "Here is a structured interview response",
                    "Here is a structured interview template",
                    "Here is a structured interview example",
                    "Here is a structured interview sample",
                    "Here is a structured interview suggestion",
                    "Here is a structured interview guidance",
                    "Here is a structured interview tip",
                    "Here is a structured interview advice",
                    "Here is a structured interview best practice",
                    "template",
                    "sample answer",
                    "example answer",
                    "generic answer",
                    "fallback answer",
                    "instructional text",
                    "structured answer",
                    "suggested answer",
                    "possible answer",
                    "general answer",
                    "response:"
                ]
                # If any forbidden phrase or template pattern is found, return an empty string
                forbidden = any(phrase.lower() in answer.lower() for phrase in forbidden_phrases)
                template_patterns = [
                    r"^answer[:\-]",
                    r"^template[:\-]",
                    r"^sample answer[:\-]",
                    r"^example[:\-]",
                    r"^suggested answer[:\-]",
                    r"^possible answer[:\-]",
                    r"^response[:\-]",
                    r"^here is",
                    r"^this is",
                    r"^let's",
                    r"^to answer",
                    r"^in summary",
                    r"^in conclusion",
                    r"^overall",
                    r"^as an? ",
                ]
                import re as _re
                template_match = any(_re.match(p, answer.strip(), _re.IGNORECASE) for p in template_patterns)
                if forbidden or template_match:
                    answer = ""
            print(f"[DEBUG] Answer returned (mode={mode}): {answer[:300]}")
            sys.stdout.flush()
            return answer
        except Exception as e:
            print(f"[DEBUG] Exception in generate_response: {e}")
            sys.stdout.flush()
            return "[Error: Could not generate answer.]"

    def build_prompt(self, question, resume_text, mode):
        # Kept for compatibility; main logic handled in generate_response
        if mode == "resume" and resume_text:
            return (
                "You are an interview assistant. Prefer resume facts to answer. If general, give concise guidance.\n"
                f"Resume:\n{resume_text}\n\nQuestion: {question}\nAnswer:"
            )
        else:
            return f"You are a helpful interview assistant.\nQuestion: {question}\nAnswer:"

    def _is_intro_question(self, question: str) -> bool:
        q = question.lower()
        patterns = [
            r"tell me about yourself",
            r"about yourself",
            r"introduce yourself",
            r"give .* introduction",
            r"self introduction",
            r"yourself",
        ]
        return any(re.search(p, q) for p in patterns)

