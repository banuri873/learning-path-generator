from flask import Flask, request, jsonify, render_template, session
from letta_client import Letta
from letta_client import MessageCreate, CreateBlock
import json
import os
import time
import uuid
from datetime import datetime


app = Flask(__name__, static_url_path='',
            static_folder='static', template_folder='templates')
# Secret key for Flask session management
app.secret_key = os.environ.get('SECRET_KEY', 'dev_secret_key')

# Initialize Letta client
client = Letta(base_url=os.environ.get(
    'LETTA_BASE_URL', 'http://localhost:8283'))

# Set the agent ID directly
AGENT_ID = "agent-dd9653df-eb47-4de5-8aac-c18187692a3e"

# User sessions to track individual user data
user_sessions = {}


def create_evaluator_agent():
    """Create a new evaluator agent with predefined questions and scoring logic"""
    try:
        # Initialize memory blocks for persistent state
        memory_blocks = [
            CreateBlock(
                label="core_instructions",
                value="""You are a Learning Path Generator specialized in evaluating programming skills and creating personalized learning roadmaps.

Your primary tasks:
1. Evaluate users based on 16 predefined questions about algorithms and data structures
2. Calculate scores for each knowledge area
3. Generate a personalized 6-week learning roadmap based on evaluation results
4. Provide detailed feedback on correct and incorrect answers
5. Return data in proper JSON format

Assessment areas include:
- Binary Search
- Two Pointers
- Breadth First Search (BFS)
- Depth First Search (DFS)/Backtracking
- Priority Queue/Heap
- Graph Algorithms
- Dynamic Programming
- Miscellaneous Algorithm Concepts

When evaluating users:
- Use ONLY the predefined questions stored in your assessment_questions_* memory blocks
- Calculate percentage-based scores for each knowledge area
- Identify strengths and weaknesses to personalize the learning path
- Provide explanations for correct answers in the review section

When generating learning paths:
- Create a 6-week structured roadmap with weekly breakdown
- Include specific topics based on evaluation results
- Provide estimated study hours per week
- Recommend resources and exercises for each topic"""
            ),
            # Split assessment questions into multiple blocks to avoid the 5000 character limit
            CreateBlock(
                label="assessment_questions_1",
                value=json.dumps([
                    {
                        "id": 1,
                        "area": "Binary Search",
                        "question": "Which type of traversal does breadth first search do?",
                        "options": [
                            {"id": "A", "text": "Level-order traversal"},
                            {"id": "B", "text": "In-order traversal"},
                            {"id": "C", "text": "Post-order traversal"},
                            {"id": "D", "text": "Pre-order traversal"}
                        ],
                        "correctAnswer": "A",
                        "explanation": "Breadth First Search traverses a tree or graph level by level, which is known as Level-order traversal."
                    },
                    {
                        "id": 2,
                        "area": "Binary Search",
                        "question": "Which algorithm should you use to find a node that is close to the root of the tree?",
                        "options": [
                            {"id": "A", "text": "Breadth First Search"},
                            {"id": "B", "text": "Depth First Search"}
                        ],
                        "correctAnswer": "A",
                        "explanation": "Breadth First Search is ideal for finding nodes close to the root since it explores nodes level by level, starting from the root."
                    },
                    {
                        "id": 3,
                        "area": "Binary Search",
                        "question": "A person thinks of a number between 1 and 1000. You may ask any number of questions, provided that the question can be answered with either 'yes' or 'no'. What is the minimum number of questions needed to guarantee you know the number?",
                        "options": [
                            {"id": "A", "text": "10"},
                            {"id": "B", "text": "8"},
                            {"id": "C", "text": "11"},
                            {"id": "D", "text": "1000"}
                        ],
                        "correctAnswer": "A",
                        "explanation": "Using binary search, you need log₂(1000) ≈ 9.97 questions, which rounds up to 10 questions."
                    },
                    {
                        "id": 4,
                        "area": "Binary Search",
                        "question": "What is the best way of checking if an element exists in a sorted array once in terms of time complexity?",
                        "options": [
                            {"id": "A", "text": "Linear Search"},
                            {"id": "B", "text": "Binary Search"},
                            {"id": "C", "text": "Quick Select"},
                            {"id": "D", "text": "Hash Set"}
                        ],
                        "correctAnswer": "B",
                        "explanation": "Binary Search has O(log n) time complexity, which is optimal for searching in a sorted array."
                    }
                ])
            ),
            CreateBlock(
                label="assessment_questions_2",
                value=json.dumps([
                    {
                        "id": 5,
                        "area": "DFS/Backtracking",
                        "question": "Which data structure is used in a depth first search?",
                        "options": [
                            {"id": "A", "text": "Stack"},
                            {"id": "B", "text": "Heap"},
                            {"id": "C", "text": "Array"},
                            {"id": "D", "text": "Queue"}
                        ],
                        "correctAnswer": "A",
                        "explanation": "Depth First Search uses a Stack data structure (or recursion, which implicitly uses the call stack)."
                    },
                    {
                        "id": 6,
                        "area": "DFS/Backtracking",
                        "question": "Which of the following problems can be solved with backtracking?",
                        "options": [
                            {"id": "A", "text": "Generating subsets"},
                            {"id": "B", "text": "Generating random numbers"},
                            {"id": "C", "text": "Sorting integers"},
                            {"id": "D", "text": "Generating permutations"}
                        ],
                        "correctAnswer": "A,D",
                        "explanation": "Backtracking is ideal for generating all possible combinations (subsets) and arrangements (permutations)."
                    },
                    {
                        "id": 7,
                        "area": "Dynamic Programming",
                        "question": "What are the two properties the problem needs to have for dynamic programming to be applicable?",
                        "options": [
                            {"id": "A", "text": "Optimal substructure"},
                            {"id": "B", "text": "Overlapping subproblems"},
                            {"id": "C", "text": "Non-overlapping subproblems"},
                            {"id": "D", "text": "Constant time subproblems"}
                        ],
                        "correctAnswer": "A,B",
                        "explanation": "Dynamic Programming requires optimal substructure (solutions can be constructed from optimal solutions to subproblems) and overlapping subproblems (same subproblems are solved multiple times)."
                    },
                    {
                        "id": 8,
                        "area": "Dynamic Programming",
                        "question": "For the longest increasing subsequence problem, what is the recurrence relation?",
                        "options": [
                            {"id": "A", "text": "dp[i] = dp[i] + 1"},
                            {"id": "B", "text": "dp[i] = dp[i] + dp[i - 1]"},
                            {"id": "C",
                                "text": "dp[i] = (dp[i] + 1) for j in 0 to i"},
                            {"id": "D",
                                "text": "dp[i] = max(dp[i], dp[j] + 1) for j in 0 to i"}
                        ],
                        "correctAnswer": "D",
                        "explanation": "The recurrence relation for LIS is dp[i] = max(dp[i], dp[j] + 1) for j in 0 to i, where dp[i] represents the length of the LIS ending at index i."
                    }
                ])
            ),
            CreateBlock(
                label="assessment_questions_3",
                value=json.dumps([
                    {
                        "id": 9,
                        "area": "Graph",
                        "question": "What's the relationship between a tree and a graph?",
                        "options": [
                            {"id": "A", "text": "No relationship"},
                            {"id": "B", "text": "A tree is a special graph"},
                            {"id": "C", "text": "A graph is a special tree"},
                            {"id": "D", "text": "They are the same thing"}
                        ],
                        "correctAnswer": "B",
                        "explanation": "A tree is a special type of graph that is connected, acyclic, and has n-1 edges for n nodes."
                    },
                    {
                        "id": 10,
                        "area": "Graph",
                        "question": "Which of the traversal algorithms can be used to find whether two nodes are connected?",
                        "options": [
                            {"id": "A", "text": "Both BFS and DFS"},
                            {"id": "B", "text": "Neither BFS nor DFS"},
                            {"id": "C", "text": "Only DFS"},
                            {"id": "D", "text": "Only BFS"}
                        ],
                        "correctAnswer": "A",
                        "explanation": "Both BFS and DFS can be used to determine if two nodes are connected in a graph by starting at one node and checking if the other node is reachable."
                    },
                    {
                        "id": 11,
                        "area": "Miscellaneous",
                        "question": "Which of the following uses divide and conquer strategy?",
                        "options": [
                            {"id": "A", "text": "Merge Sort"},
                            {"id": "B", "text": "Insertion sort"},
                            {"id": "C", "text": "Heap sort"},
                            {"id": "D", "text": "Bubble sort"}
                        ],
                        "correctAnswer": "A",
                        "explanation": "Merge Sort is a classic divide and conquer algorithm that splits the array in half, recursively sorts each half, and then merges the sorted halves."
                    },
                    {
                        "id": 12,
                        "area": "Miscellaneous",
                        "question": "How does quick sort divide the problem into subproblems?",
                        "options": [
                            {"id": "A", "text": "Divide the array into a stray element and the rest of the array"},
                            {"id": "B", "text": "Divide the array into two based on whether an element is smaller than an arbitrary value"},
                            {"id": "C", "text": "Divide the array into two equal halves by index"},
                            {"id": "D", "text": "Quick sort does not use divide and conquer"}
                        ],
                        "correctAnswer": "B",
                        "explanation": "Quick Sort divides the array into two parts based on a pivot value: elements smaller than the pivot and elements greater than the pivot."
                    }
                ])
            ),
            CreateBlock(
                label="assessment_questions_4",
                value=json.dumps([
                    {
                        "id": 13,
                        "area": "Priority Queue/Heap",
                        "question": "A heap is a ...?",
                        "options": [
                            {"id": "A", "text": "Hash Table"},
                            {"id": "B", "text": "Array"},
                            {"id": "C", "text": "Queue"},
                            {"id": "D", "text": "Tree"}
                        ],
                        "correctAnswer": "D",
                        "explanation": "A heap is a specialized tree-based data structure (specifically a complete binary tree) that satisfies the heap property."
                    },
                    {
                        "id": 14,
                        "area": "Two Pointers",
                        "question": "Which two pointer techniques do you use to check if a string is a palindrome?",
                        "options": [
                            {"id": "A", "text": "Two pointers moving in opposite direction"},
                            {"id": "B", "text": "Prefix sum"},
                            {"id": "C", "text": "Fast-slow pointers"},
                            {"id": "D", "text": "Sliding window"}
                        ],
                        "correctAnswer": "A",
                        "explanation": "To check if a string is a palindrome, use two pointers - one starting from the beginning and the other from the end, moving towards each other and comparing characters."
                    },
                    {
                        "id": 15,
                        "area": "Miscellaneous",
                        "question": "What does the following code do?\n```python\ndef f(arr1, arr2):\n    i, j = 0, 0\n    new_arr = []\n    while i < len(arr1) and j < len(arr2):\n        if arr1[i] < arr2[j]:\n            new_arr.append(arr1[i])\n            i += 1\n        else:\n            new_arr.append(arr2[j])\n            j += 1\n    new_arr.extend(arr1[i:])\n    new_arr.extend(arr2[j:])\n    return new_arr\n```",
                        "options": [
                            {"id": "A", "text": "Find the intersection of two arrays"},
                            {"id": "B", "text": "Finding median values of 2 arrays"},
                            {"id": "C", "text": "Check if one array is a subsequence of the other"},
                            {"id": "D", "text": "Merge two sorted arrays"}
                        ],
                        "correctAnswer": "D",
                        "explanation": "This code implements the merge step of merge sort, combining two sorted arrays into a single sorted array by comparing elements and taking the smaller one each time."
                    },
                    {
                        "id": 16,
                        "area": "BFS",
                        "question": "What data structure is primarily used in Breadth First Search?",
                        "options": [
                            {"id": "A", "text": "Stack"},
                            {"id": "B", "text": "Queue"},
                            {"id": "C", "text": "Linked List"},
                            {"id": "D", "text": "Hash Table"}
                        ],
                        "correctAnswer": "B",
                        "explanation": "Breadth First Search uses a Queue data structure to keep track of nodes to visit next, ensuring that nodes are processed in level order."
                    }
                ])
            ),
            CreateBlock(
                label="user_history",
                value=json.dumps({
                    "evaluations_completed": 0,
                    "last_evaluation": None,
                    "roadmaps_generated": 0
                })
            ),
            CreateBlock(
                label="scoring_logic",
                value=json.dumps({
                    "knowledge_areas": [
                        "Binary Search",
                        "Two Pointers",
                        "BFS",
                        "DFS/Backtracking",
                        "Priority Queue/Heap",
                        "Graph",
                        "Dynamic Programming",
                        "Miscellaneous"
                    ],
                    "weight_by_area": {
                        "Binary Search": 1.0,
                        "Two Pointers": 1.0,
                        "BFS": 1.0,
                        "DFS/Backtracking": 1.0,
                        "Priority Queue/Heap": 1.0,
                        "Graph": 1.0,
                        "Dynamic Programming": 1.0,
                        "Miscellaneous": 1.0
                    },
                    "recommended_levels": {
                        "Binary Search": 80,
                        "Two Pointers": 75,
                        "BFS": 70,
                        "DFS/Backtracking": 65,
                        "Priority Queue/Heap": 70,
                        "Graph": 65,
                        "Dynamic Programming": 60,
                        "Miscellaneous": 75
                    }
                })
            ),
            CreateBlock(
                label="roadmap_templates",
                value=json.dumps({
                    "beginner": {
                        "title": "Beginner's Path to Algorithmic Mastery",
                        "weekly_structure": [
                            {
                                "week": 1,
                                "focus": "Foundations",
                                "hours_per_week": 10,
                                "modules": 3,
                                "lessons": 6
                            },
                            {
                                "week": 2,
                                "focus": "Basic Data Structures",
                                "hours_per_week": 12,
                                "modules": 4,
                                "lessons": 8
                            },
                            {
                                "week": 3,
                                "focus": "Searching Algorithms",
                                "hours_per_week": 12,
                                "modules": 3,
                                "lessons": 9
                            },
                            {
                                "week": 4,
                                "focus": "Sorting Algorithms",
                                "hours_per_week": 14,
                                "modules": 4,
                                "lessons": 12
                            },
                            {
                                "week": 5,
                                "focus": "Graph Basics",
                                "hours_per_week": 14,
                                "modules": 3,
                                "lessons": 9
                            },
                            {
                                "week": 6,
                                "focus": "Introduction to Dynamic Programming",
                                "hours_per_week": 15,
                                "modules": 4,
                                "lessons": 8
                            }
                        ]
                    },
                    "intermediate": {
                        "title": "Intermediate Algorithm Advancement",
                        "weekly_structure": [
                            {
                                "week": 1,
                                "focus": "Advanced Data Structures",
                                "hours_per_week": 12,
                                "modules": 4,
                                "lessons": 8
                            },
                            {
                                "week": 2,
                                "focus": "Binary Search Applications",
                                "hours_per_week": 14,
                                "modules": 3,
                                "lessons": 9
                            },
                            {
                                "week": 3,
                                "focus": "Depth-First and Breadth-First Search",
                                "hours_per_week": 15,
                                "modules": 4,
                                "lessons": 12
                            },
                            {
                                "week": 4,
                                "focus": "Dynamic Programming Patterns",
                                "hours_per_week": 16,
                                "modules": 4,
                                "lessons": 8
                            },
                            {
                                "week": 5,
                                "focus": "Advanced Graph Algorithms",
                                "hours_per_week": 15,
                                "modules": 3,
                                "lessons": 9
                            },
                            {
                                "week": 6,
                                "focus": "Problem-Solving Strategies",
                                "hours_per_week": 14,
                                "modules": 4,
                                "lessons": 10
                            }
                        ]
                    },
                    "advanced": {
                        "title": "Advanced Algorithm Mastery",
                        "weekly_structure": [
                            {
                                "week": 1,
                                "focus": "Complex Data Structures",
                                "hours_per_week": 15,
                                "modules": 4,
                                "lessons": 10
                            },
                            {
                                "week": 2,
                                "focus": "Advanced Binary Search Techniques",
                                "hours_per_week": 16,
                                "modules": 3,
                                "lessons": 9
                            },
                            {
                                "week": 3,
                                "focus": "Advanced Graph Theory",
                                "hours_per_week": 18,
                                "modules": 4,
                                "lessons": 12
                            },
                            {
                                "week": 4,
                                "focus": "Dynamic Programming Optimization",
                                "hours_per_week": 20,
                                "modules": 5,
                                "lessons": 15
                            },
                            {
                                "week": 5,
                                "focus": "Advanced Algorithm Design",
                                "hours_per_week": 18,
                                "modules": 4,
                                "lessons": 12
                            },
                            {
                                "week": 6,
                                "focus": "Competitive Programming Strategies",
                                "hours_per_week": 15,
                                "modules": 4,
                                "lessons": 10
                            }
                        ]
                    }
                })
            )
        ]

        agent = client.agents.create(
            name="LearningPathGenerator",
            system="""You are a Learning Path Generator specialized in evaluating programming skills and creating personalized learning roadmaps.

You have multiple memory blocks:
1. core_instructions - Contains your operation guidelines
2. assessment_questions_1 through assessment_questions_4 - Contain the 16 predefined assessment questions split across blocks
3. user_history - Tracks user interactions and evaluations
4. scoring_logic - Contains scoring weights and recommended levels
5. roadmap_templates - Contains templates for generating personalized roadmaps

When conducting evaluations:
1. Use ONLY the questions from the assessment_questions_* memory blocks
2. Calculate scores based on the scoring_logic for each knowledge area
3. After an evaluation, update the user_history with the results
4. Generate detailed feedback for each question with explanations
5. Create a personalized learning roadmap based on the evaluation results

Always return data in properly formatted JSON to ensure compatibility with the frontend.

Your tone should be professional, encouraging, and educational.""",
            agent_type="chat_only_agent",
            memory_blocks=memory_blocks,
            llm_config={
                "model": "claude-3-5-sonnet-20241022",
                "model_endpoint_type": "anthropic",
                "temperature": 0.7,
                "context_window": 16000,
                "max_tokens": 4000
            },
            embedding_config={
                "embedding_model": "text-embedding-ada-002",
                "embedding_endpoint_type": "openai",
                "embedding_dim": 1536
            },
            description="An evaluator that assesses programming knowledge and creates personalized learning paths"
        )

        # Wait a moment for the agent to initialize fully
        time.sleep(2)

        print(f"Agent created successfully with ID: {agent.id}")
        return agent.id
    except Exception as e:
        print(f"Error creating agent: {e}")
        return None


def extract_assistant_message(response):
    """Extract message content from different response formats"""
    if hasattr(response, 'assistant_message'):
        return response.assistant_message.content
    elif hasattr(response, 'messages'):
        for msg in response.messages:
            # Check for assistant message type
            if hasattr(msg, 'message_type') and msg.message_type == 'assistant_message':
                return msg.content

            # Check other message attributes
            if hasattr(msg, 'content'):
                if isinstance(msg.content, list):
                    for content_item in msg.content:
                        if isinstance(content_item, dict) and content_item.get('type') == 'text':
                            return content_item.get('text')
                else:
                    return msg.content
    return "No response found"


def get_or_create_agent():
    """Get the existing agent or create a new one if needed"""
    global AGENT_ID

    # Try to retrieve the agent to confirm it exists
    try:
        agent = client.agents.retrieve(agent_id=AGENT_ID)
        print(f"Using existing agent: {AGENT_ID}")
        return AGENT_ID
    except Exception as e:
        print(f"Error retrieving agent: {e}")
        print("Will create a new agent")

        # Create a new agent
        new_agent_id = create_evaluator_agent()
        if new_agent_id:
            AGENT_ID = new_agent_id
            print(f"New agent created with ID: {AGENT_ID}")
        else:
            print("Failed to create agent")

        return AGENT_ID


def get_user_id():
    """Get or create user ID from session"""
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
        print(f"Created new user ID: {session['user_id']}")

    user_id = session['user_id']

    # Ensure user session data exists
    if user_id not in user_sessions:
        print(f"Initializing session data for user: {user_id}")
        # Initialize user session data
        user_sessions[user_id] = {
            'experience': None,
            'education': None,
            'goal': None,
            'questions': [],
            'answers': [],
            'score': None,
            'areas': {},
            'roadmap': None,
            'session_start': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    return user_id


def update_agent_memory(agent_id, user_id, evaluation_data=None):
    """Update agent's memory with user's evaluation data"""
    try:
        # Prepare update for user history
        if evaluation_data:
            history_update = {
                "evaluations_completed": user_sessions[user_id].get('evaluations_completed', 0) + 1,
                "last_evaluation": {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "user_id": user_id,
                    "scores": evaluation_data.get("areas", {}),
                    "overall_score": evaluation_data.get("score", 0)
                },
                "roadmaps_generated": user_sessions[user_id].get('roadmaps_generated', 0) + 1
            }
        else:
            # Just retrieve current history if no new data
            return True

        # Force memory update by creating a special message that updates memory
        update_message = MessageCreate(
            role="user",
            content=f"""[SYSTEM MEMORY APPEND]
Please append your user_history memory block with the following information:

{json.dumps(history_update, indent=2)}

Please respond with "Memory appended" once you've noted these changes."""
        )

        # Send the update message without use_assistant_message flag
        print("Updating agent memory...")
        response = client.agents.messages.create(
            agent_id=agent_id,
            messages=[update_message]
        )
        print("Memory update response received")

        print(f"Memory updated for user: {user_id}")
        return True

    except Exception as e:
        print(f"Error updating agent memory: {e}")
        return False


@app.route('/')
def index():
    # Get or create user ID
    user_id = get_user_id()

    # Pass user session data to the template
    user_data = user_sessions.get(user_id, {})
    return render_template('index.html', user_data=user_data)


@app.route('/api/save_profile', methods=['POST'])
def save_profile():
    """Save initial user profile information"""
    data = request.json
    experience = data.get('experience')
    education = data.get('education')
    goal = data.get('goal')

    if not all([experience, education, goal]):
        return jsonify({"error": "All profile fields are required"}), 400

    # Get user ID
    user_id = get_user_id()

    # Ensure user session exists (should be created by get_user_id, but double-check)
    if user_id not in user_sessions:
        # Re-initialize session data if it's missing
        user_sessions[user_id] = {
            'experience': None,
            'education': None,
            'goal': None,
            'questions': [],
            'answers': [],
            'score': None,
            'areas': {},
            'roadmap': None,
            'session_start': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    # Save profile data
    user_sessions[user_id]['experience'] = experience
    user_sessions[user_id]['education'] = education
    user_sessions[user_id]['goal'] = goal

    return jsonify({"success": True})


@app.route('/api/get_questions', methods=['GET'])
def get_questions():
    """Get assessment questions from the agent"""
    # Get or create agent
    agent_id = get_or_create_agent()
    if not agent_id:
        return jsonify({"error": "Failed to create or retrieve agent"}), 500

    # Get user ID
    user_id = get_user_id()
    print(f"Getting questions for user: {user_id}")

    # Create message to get questions
    message = MessageCreate(
        role="user",
        content="""Perform a comprehensive memory block search:
1. Carefully archive and preserve existing assessment questions 
2. Verify core_instructions for question generation guidelines
3. Ensure NO EXISTING QUESTIONS ARE DELETED during retrieval
4. Maintain historical question context
5. Use archival retrieval methodology
        
        Now Please combine all the questions from your assessment_questions_1, assessment_questions_2, assessment_questions_3, and assessment_questions_4 memory blocks and Return ONLY a JSON object with this structure:
{
  "questions": [
    {
      "id": 1,
      "question": "Question text",
      "options": [
        {"id": "A", "text": "Option A"},
        {"id": "B", "text": "Option B"},
        {"id": "C", "text": "Option C"},
        {"id": "D", "text": "Option D"}
      ],
      "correctAnswer": "A"
    }
    // ... more questions
  ]
}
        

Do not include any additional text or markdown code blocks."""
    )

    try:
        # Send message to agent
        print("Sending message to agent...")
        response = client.agents.messages.create(
            agent_id=agent_id,
            messages=[message],
            use_assistant_message=True
        )
        print("Response received from agent")

        # Extract the message content
        assistant_msg = extract_assistant_message(response)

        # Remove any potential markdown code block markers
        if assistant_msg.startswith("```json"):
            assistant_msg = assistant_msg[7:]
        if assistant_msg.endswith("```"):
            assistant_msg = assistant_msg[:-3]

        # Parse the JSON
        try:
            questions_data = json.loads(assistant_msg.strip())

            # Store questions in user session
            user_sessions[user_id]['questions'] = questions_data.get(
                'questions', [])

            return jsonify(questions_data)
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Raw response: {assistant_msg}")
            return jsonify({"error": "Failed to parse questions data"}), 500

    except Exception as e:
        print(f"Error getting questions: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/submit_answers', methods=['POST'])
def submit_answers():
    """Submit user answers for evaluation"""
    data = request.json
    answers = data.get('answers')

    if not answers:
        return jsonify({"error": "Answers are required"}), 400

    # Get user ID
    user_id = get_user_id()
    print(f"Submitting answers for user: {user_id}")

    # Verify the user session exists
    if user_id not in user_sessions:
        print(
            f"Warning: User session not found for ID {user_id}, reinitializing")
        user_sessions[user_id] = {
            'experience': None,
            'education': None,
            'goal': None,
            'questions': [],
            'answers': [],
            'score': None,
            'areas': {},
            'roadmap': None,
            'session_start': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    # Save answers
    user_sessions[user_id]['answers'] = answers

    # Get or create agent
    agent_id = get_or_create_agent()
    if not agent_id:
        return jsonify({"error": "Failed to create or retrieve agent"}), 500

    # Get questions from user session
    questions = user_sessions[user_id].get('questions', [])
    if not questions:
        return jsonify({"error": "No questions found for evaluation"}), 400

    # Create input for evaluation
    evaluation_input = {
        "questions": questions,
        "answers": answers,
        "user_profile": {
            "experience": user_sessions[user_id].get('experience'),
            "education": user_sessions[user_id].get('education'),
            "goal": user_sessions[user_id].get('goal')
        }
    }

    # Create message for evaluation
    message = MessageCreate(
        role="user",
        content=f""" Comprehensive Memory Block Evaluation Protocol:

Memory Search Guidelines:
1. Conduct thorough archival search across memory blocks
2. Review scoring_logic for persistent knowledge area weights
3. Examine user_history for previous interaction context
4. Verify core_instructions for evaluation methodology

Archival Retrieval Instructions:
- Preserve ALL historical evaluation data
- Append new evaluation results to existing records
- Maintain comprehensive user interaction history

Now, evaluate the user's answers based on the following data:
        Please evaluate the user's answers based on the following data:

{json.dumps(evaluation_input, indent=2)}

For each knowledge area, calculate the percentage of correct answers.
Create a detailed evaluation with the following structure:
1. Overall score (percentage of all correct answers)
2. Area-by-area breakdown with scores and personalized feedback
3. Compare the user's scores with the recommended levels

Return the evaluation as a JSON object with this structure:
{{
  "score": 75,
  "areas": {{
    "Binary Search": {{
      "score": 80,
      "recommended": 80,
      "feedback": "You have a good understanding of binary search concepts."
    }},
    ...other areas...
  }},
  "review": [
    {{
      "question_id": 1,
      "correct": true,
      "user_answer": "A",
      "explanation": "Detailed explanation here..."
    }},
    ...other questions...
  ]
}}

Only respond with the JSON object, no additional text."""
    )

    try:
        # Send message to agent
        print("Sending evaluation request to agent...")
        response = client.agents.messages.create(
            agent_id=agent_id,
            messages=[message]
        )
        print("Evaluation response received from agent")

        assistant_msg = extract_assistant_message(response)

        # Process the response to extract JSON
        try:
            # Find JSON content
            if "```json" in assistant_msg:
                json_start = assistant_msg.find("```json") + 7
                json_end = assistant_msg.find("```", json_start)
                json_content = assistant_msg[json_start:json_end].strip()
                evaluation_data = json.loads(json_content)
            else:
                # Try to extract JSON directly
                first_brace = assistant_msg.find('{')
                last_brace = assistant_msg.rfind('}')

                if first_brace >= 0 and last_brace > first_brace:
                    json_content = assistant_msg[first_brace:last_brace+1]
                    evaluation_data = json.loads(json_content)
                else:
                    evaluation_data = json.loads(assistant_msg)

            # Store evaluation in user session
            user_sessions[user_id]['score'] = evaluation_data.get('score')
            user_sessions[user_id]['areas'] = evaluation_data.get('areas', {})
            user_sessions[user_id]['review'] = evaluation_data.get(
                'review', [])

            # Update agent memory with evaluation data
            update_agent_memory(agent_id, user_id, evaluation_data)

            return jsonify(evaluation_data)
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Raw response: {assistant_msg}")
            return jsonify({"error": "Failed to parse evaluation data"}), 500

    except Exception as e:
        print(f"Error evaluating answers: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/generate_roadmap', methods=['GET'])
def generate_roadmap():
    """Generate a personalized learning roadmap based on evaluation results"""
    # Get user ID
    user_id = get_user_id()
    print(f"Generating roadmap for user: {user_id}")

    # Verify the user session exists
    if user_id not in user_sessions:
        print(
            f"Warning: User session not found for ID {user_id}, reinitializing")
        return jsonify({"error": "Session expired. Please complete the evaluation first"}), 400

    # Check if user has completed the evaluation
    if not user_sessions[user_id].get('score'):
        return jsonify({"error": "Please complete the evaluation first"}), 400

    # Get or create agent
    agent_id = get_or_create_agent()
    if not agent_id:
        return jsonify({"error": "Failed to create or retrieve agent"}), 500

    # Create input for roadmap generation
    roadmap_input = {
        "user_profile": {
            "experience": user_sessions[user_id].get('experience'),
            "education": user_sessions[user_id].get('education'),
            "goal": user_sessions[user_id].get('goal')
        },
        "evaluation": {
            "score": user_sessions[user_id].get('score'),
            "areas": user_sessions[user_id].get('areas', {})
        }
    }

    # Create message for roadmap generation
    message = MessageCreate(
        role="user",
        content=f""" Memory Block Archival Search:
1. Conduct extensive review of roadmap_templates
2. Archive and preserve existing roadmap structures
3. Examine scoring_logic for persistent knowledge weightings
4. Review user_history for comprehensive interaction context
5. Verify core_instructions for roadmap generation methodology
Please generate a personalized 6-week learning roadmap based on the following evaluation:

{json.dumps(roadmap_input, indent=2)}

Use the roadmap_templates in your memory to select an appropriate template based on the user's overall score:
- Below 50%: beginner template
- 50-75%: intermediate template
- Above 75%: advanced template

Then, customize the template based on the user's strengths and weaknesses in different knowledge areas.

Return the roadmap as a JSON object with this structure:
{{
  "title": "Here's a Straightforward Roadmap to Success",
  "level": "Intermediate",
  "overall_score": 75,
  "weeks": [
    {{
      "week": 1,
      "focus": "Advanced Data Structures",
      "hours": 12,
      "modules": 4,
      "lessons": 8,
      "topics": [
        "Priority Queues",
        "Advanced Hash Tables",
        "Segment Trees"
      ],
      "resources": [
        {{
          "type": "Tutorial",
          "title": "Introduction to Advanced Data Structures",
          "url": "https://example.com/tutorial"
        }}
      ]
    }},
    ...other weeks...
  ]
}}

Ensure that:
1. Each week addresses specific knowledge areas that need improvement
2. The roadmap is progressive and builds skills week by week
3. Resources are specific and relevant to the topics
4. The hours, modules, and lessons are realistic based on the template

Only respond with the JSON object, no additional text."""
    )

    try:
        # Send message to agent without use_assistant_message flag
        print("Sending roadmap request to agent...")
        response = client.agents.messages.create(
            agent_id=agent_id,
            messages=[message]
        )
        print("Roadmap response received from agent")

        assistant_msg = extract_assistant_message(response)

        # Process the response to extract JSON
        try:
            # Find JSON content
            if "```json" in assistant_msg:
                json_start = assistant_msg.find("```json") + 7
                json_end = assistant_msg.find("```", json_start)
                json_content = assistant_msg[json_start:json_end].strip()
                roadmap_data = json.loads(json_content)
            else:
                # Try to extract JSON directly
                first_brace = assistant_msg.find('{')
                last_brace = assistant_msg.rfind('}')

                if first_brace >= 0 and last_brace > first_brace:
                    json_content = assistant_msg[first_brace:last_brace+1]
                    roadmap_data = json.loads(json_content)
                else:
                    roadmap_data = json.loads(assistant_msg)

            # Store roadmap in user session
            user_sessions[user_id]['roadmap'] = roadmap_data
            user_sessions[user_id]['roadmaps_generated'] = user_sessions[user_id].get(
                'roadmaps_generated', 0) + 1

            return jsonify(roadmap_data)
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Raw response: {assistant_msg}")
            return jsonify({"error": "Failed to parse roadmap data"}), 500

    except Exception as e:
        print(f"Error generating roadmap: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/clear_session', methods=['POST'])
def clear_session():
    """Clear the current user session for testing"""
    # Get user ID
    user_id = get_user_id()

    # Reset session data
    user_sessions[user_id] = {
        'experience': None,
        'education': None,
        'goal': None,
        'questions': [],
        'answers': [],
        'score': None,
        'areas': {},
        'roadmap': None,
        'session_start': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    return jsonify({"success": True})


@app.route('/api/chat', methods=['POST'])
def chat_with_agent():
    """Send a chat message to the agent and get a response"""
    data = request.json
    message = data.get('message')
    context = data.get('context', {})

    if not message:
        return jsonify({"error": "Message is required"}), 400

    # Get user ID
    user_id = get_user_id()
    print(f"Chat message from user: {user_id}")

    # Get or create agent
    agent_id = get_or_create_agent()
    if not agent_id:
        return jsonify({"error": "Failed to create or retrieve agent"}), 500

    # Add context about the user and their progress
    context_prompt = ""
    if context.get('experience'):
        context_prompt += f"User experience level: {context.get('experience')}\n"
    if context.get('education'):
        context_prompt += f"Computer science background: {context.get('education')}\n"
    if context.get('goal'):
        context_prompt += f"User's goal: {context.get('goal')}\n"

    # Add evaluation results if available
    if context.get('evaluationResults'):
        results = context.get('evaluationResults')
        context_prompt += f"\nEvaluation results:\n"
        context_prompt += f"Overall score: {results.get('score')}%\n"
        context_prompt += "Knowledge area scores:\n"
        for area, data in results.get('areas', {}).items():
            context_prompt += f"- {area}: {data.get('score')}% (recommended: {data.get('recommended')}%)\n"

    # Add roadmap info if available
    if context.get('roadmapData'):
        roadmap = context.get('roadmapData')
        context_prompt += f"\nCurrent learning path: {roadmap.get('title')}\n"
        context_prompt += f"Level: {roadmap.get('level')}\n"

    # Create the full message with context
    formatted_message = f"""
[CONVERSATION CONTEXT]
{context_prompt}

[USER QUESTION]
{message}

Please respond conversationally as the Learning Path Generator assistant. Format any code with markdown code blocks using triple backticks. Keep responses concise, educational and encouraging. If the user asks about technical concepts, provide accurate but accessible explanations.
"""

    # Create message for agent
    chat_message = MessageCreate(
        role="user",
        content=formatted_message
    )

    try:
        # Send message to agent
        print("Sending chat message to agent...")
        response = client.agents.messages.create(
            agent_id=agent_id,
            messages=[chat_message]
        )
        print("Chat response received from agent")

        # Extract the assistant message
        assistant_msg = extract_assistant_message(response)

        # Save chat to user session if not already tracking chats
        if 'chat_history' not in user_sessions[user_id]:
            user_sessions[user_id]['chat_history'] = []

        # Add to chat history
        user_sessions[user_id]['chat_history'].append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        user_sessions[user_id]['chat_history'].append({
            'role': 'assistant',
            'content': assistant_msg,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        return jsonify({
            "response": assistant_msg
        })

    except Exception as e:
        print(f"Error chatting with agent: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # Check if the agent exists at startup
    try:
        agent = client.agents.retrieve(agent_id=AGENT_ID)
        print(f"Confirmed existing agent: {AGENT_ID}")
    except Exception as e:
        print(f"Warning: Could not retrieve agent: {e}")
        print("A new agent will be created when needed.")
