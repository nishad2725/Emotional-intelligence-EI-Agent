# 🧠 Emotional Intelligence AI Agent

An intelligent AI-powered emotional intelligence assistant that analyzes text emotions, provides personalized coaching, and helps users develop their emotional awareness through advanced AI workflows.

## ✨ Features

### 🎯 Core Capabilities
- **Text Emotion Analysis**: Advanced emotion detection using GPT-4 with valence, arousal, and primary emotion identification
- **Toxicity Detection**: Google Perspective API integration for content safety analysis
- **Personalized Coaching**: AI-powered emotional intelligence coaching with practical exercises
- **Quality Evaluation**: Automated coaching quality assessment with refinement capabilities
- **Session Logging**: Firebase integration for comprehensive session tracking

### 🔄 Intelligent Workflow
The system uses LangGraph to orchestrate a sophisticated pipeline:
1. **Analyze** → Extract emotions and toxicity from user input
2. **Coach** → Generate personalized EI coaching advice
3. **Evaluate** → Assess coaching quality (empathy, specificity, safety)
4. **Refine** → Automatically improve coaching if quality is low
5. **Persist** → Log session data for analysis and improvement

## 🏗️ Architecture

```
backend/
├── agents/
│   └── ei_graph.py          # Main LangGraph workflow orchestration
├── services/
│   ├── openai_client.py     # OpenAI API client management
│   ├── perspective.py       # Google Perspective API integration
│   ├── firebase.py          # Firebase Firestore session logging
│   └── hume_voice.py        # Voice analysis (Phase 2+)
├── skills/
│   ├── text_emotion.py      # Emotion analysis using GPT-4
│   ├── coach.py             # AI coaching response generation
│   └── evaluator.py         # Coaching quality evaluation
├── config.py                # Environment configuration
└── cli.py                   # Command-line interface
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key
- Google Perspective API key
- Firebase project with Firestore enabled

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/nishad2725/ei-assistant.git
   cd ei-assistant
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Set up Firebase**
   - Download your Firebase service account key
   - Save as `serviceAccountKey.json` in the project root

### Configuration

Edit your `.env` file with the required API keys:

```env
OPENAI_API_KEY=sk-your-openai-key
GOOGLE_PERSPECTIVE_API_KEY=your-perspective-key
FIREBASE_PROJECT_ID=your-firebase-project-id
GOOGLE_APPLICATION_CREDENTIALS=./serviceAccountKey.json
HUME_API_KEY=your-hume-key  # Optional for Phase 2
```

## 🎮 Usage

### Command Line Interface

Run the interactive CLI to test the system:

```bash
python -m backend.cli
```

Example interaction:
```
=========================
 EI Assistant (Phase 1)
=========================
(type 'quit' to exit)

How are you feeling today? I'm feeling overwhelmed with work and stressed about deadlines

— Coach —
I can hear that work pressure is really weighing on you right now. 
Try the 4-7-8 breathing technique: inhale for 4 counts, hold for 7, exhale for 8. 
This can help reset your nervous system and give you clarity for prioritizing tasks.
```

### Programmatic Usage

```python
from backend.agents.ei_graph import ei_graph

# Analyze user input
result = ei_graph.invoke({"user_text": "I'm feeling anxious about the presentation tomorrow"})

# Access results
emotion_data = result["emotion"]
coaching_advice = result["coaching"]
quality_evaluation = result["eval"]
```

## 🔧 API Integrations

### OpenAI GPT-4
- **Emotion Analysis**: Extracts valence, arousal, primary emotions, and confidence scores
- **Coaching Generation**: Creates personalized EI exercises and advice
- **Quality Evaluation**: Assesses coaching effectiveness

### Google Perspective API
- **Toxicity Detection**: Identifies potentially harmful or inappropriate content
- **Safety Filtering**: Ensures coaching responses are appropriate and safe

### Firebase Firestore
- **Session Logging**: Comprehensive tracking of user interactions
- **Data Analytics**: Enables analysis of emotional patterns and coaching effectiveness
- **Privacy-First**: Configurable data retention and anonymization

## 📊 Emotion Analysis Output

The system provides detailed emotional analysis:

```json
{
  "valence": 0.2,           // Emotional positivity (-1 to 1)
  "arousal": 0.8,           // Emotional intensity (0 to 1)
  "primary_emotions": ["anxiety", "overwhelm"],
  "confidence": 0.92,       // Analysis confidence (0 to 1)
  "rationale": "Text indicates high stress and worry about future events"
}
```

## 🛡️ Safety & Quality

### Multi-Layer Quality Control
- **Empathy Assessment**: Ensures coaching responses are emotionally supportive
- **Specificity Evaluation**: Validates that advice is actionable and specific
- **Safety Checks**: Confirms responses are appropriate and non-harmful
- **Automatic Refinement**: Low-quality responses are automatically improved

### Privacy & Security
- **No Data Storage**: User text is not permanently stored (configurable)
- **Secure API Keys**: Environment-based configuration
- **Firebase Security**: Configurable Firestore security rules

## 🗺️ Roadmap

### Phase 1 (Current)
- ✅ Text-based emotion analysis
- ✅ AI coaching with quality evaluation
- ✅ Firebase session logging
- ✅ CLI interface

### Phase 2 (Planned)
- 🔄 Voice emotion analysis with Hume AI
- 🔄 Real-time conversation capabilities
- 🔄 Advanced emotion tracking over time
- 🔄 Personalized emotion coaching plans

### Phase 3 (Future)
- 📱 Web application interface
- 📱 Mobile app integration
- 📱 Team/group emotional intelligence features
- 📱 Advanced analytics dashboard

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI** for GPT-4 emotion analysis capabilities
- **Google** for Perspective API toxicity detection
- **LangGraph** for workflow orchestration
- **Firebase** for session data management

## 📞 Support

For support, questions, or feature requests:
- Open an issue on GitHub
- Contact: [Your Contact Information]

---

**Built with ❤️ for emotional intelligence and mental wellness**
