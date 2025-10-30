#!/usr/bin/env python
"""
Test script for AyuPilot AI Assistant
Run this to verify your OpenAI API key is working
"""
import os
import sys

def test_openai_connection():
    """Test OpenAI API connection"""
    print("🧪 Testing AyuPilot AI Assistant Setup...\n")
    
    # Check if openai is installed
    try:
        from openai import OpenAI
        print("✅ OpenAI package installed")
    except ImportError:
        print("❌ OpenAI package not installed")
        print("   Run: pip install openai==1.54.0")
        return False
    
    # Check for API key
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        print("\n📋 Setup Instructions:")
        print("   1. Get API key from: https://platform.openai.com/api-keys")
        print("   2. Set environment variable:")
        print("      PowerShell: $env:OPENAI_API_KEY='sk-your-key-here'")
        print("      Linux/Mac: export OPENAI_API_KEY='sk-your-key-here'")
        print("   3. Or create .env file with: OPENAI_API_KEY=sk-your-key-here")
        return False
    
    print(f"✅ API key found (starts with: {api_key[:15]}...)")
    
    # Test API call
    try:
        print("\n🤖 Testing API call to OpenAI...")
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful Ayurvedic assistant."
                },
                {
                    "role": "user",
                    "content": "Say hello in one sentence."
                }
            ],
            max_tokens=50
        )
        
        ai_response = response.choices[0].message.content
        print(f"✅ API call successful!")
        print(f"\n💬 AI Response: {ai_response}\n")
        
        print("=" * 60)
        print("🎉 SUCCESS! Your AI Assistant is ready to use!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Make sure Django backend is running")
        print("2. Make sure Celery worker is running:")
        print("   celery -A src worker -l INFO")
        print("3. Make sure Redis is running")
        print("4. Open the frontend and test the AI assistant chat")
        return True
        
    except Exception as e:
        print(f"❌ API call failed: {str(e)}")
        print("\n🔍 Troubleshooting:")
        print("   - Verify API key is correct")
        print("   - Check OpenAI account has credits")
        print("   - Visit: https://platform.openai.com/account/billing")
        return False

if __name__ == "__main__":
    success = test_openai_connection()
    sys.exit(0 if success else 1)
