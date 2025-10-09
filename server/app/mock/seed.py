"""
Database seeding script for generating mock chat sessions and messages.
This script populates the database with realistic conversation data for testing purposes.
"""

import random
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.db.database import SessionLocal, engine
from app.models.chat_session import Base, ChatSession, Message, TypeEnum

# Sample conversation topics and responses
CONVERSATION_TOPICS = [
  "Data Analysis Help",
  "Python Programming Questions",
  "Machine Learning Project",
  "Web Development Support",
  "API Integration Issues",
  "Database Design Discussion",
  "Code Review Session",
  "Bug Troubleshooting",
  "Performance Optimization",
  "System Architecture Planning",
  "Sales Data Visualization",
  "Revenue Trend Analysis",
  "User Growth Metrics",
  "Product Performance Review",
  "Financial Dashboard Setup",
]

SAMPLE_USER_MESSAGES = [
  "Hi, I need help with my project",
  "Can you explain how this works?",
  "I'm getting an error in my code",
  "What's the best approach for this problem?",
  "How can I optimize this function?",
  "Can you review my implementation?",
  "I'm stuck on this algorithm",
  "What library should I use for this?",
  "How do I handle this edge case?",
  "Can you help me debug this issue?",
  "What's wrong with my SQL query?",
  "How do I implement this feature?",
  "Can you suggest a better design pattern?",
  "I need help with data visualization",
  "How can I improve the performance?",
  "Can you create a chart of our sales data?",
  "Show me the revenue trends over time",
  "Generate a bar chart for product comparison",
  "I need a visualization of user growth",
  "Create a line chart for quarterly performance",
]

SAMPLE_ASSISTANT_MESSAGES = [
  "I'd be happy to help you with that! Let me take a look at your code.",
  "That's a great question. Here's how you can approach this problem:",
  "I see the issue. The error is occurring because of a type mismatch.",
  "For this use case, I'd recommend using a different approach:",
  "You can optimize this by implementing caching and reducing database calls.",
  "Your implementation looks good overall, but here are some suggestions:",
  "This is a common problem. Here's a step-by-step solution:",
  "For this type of task, I'd suggest using pandas or numpy.",
  "You'll want to add proper error handling for edge cases like empty inputs.",
  "The issue is in your loop logic. Try this instead:",
  "Your query needs a JOIN clause to get the related data.",
  "You can implement this feature using a factory pattern.",
  "Consider using dependency injection for better testability.",
  "For data visualization, I recommend using matplotlib or plotly.",
  "To improve performance, consider using async operations and connection pooling.",
]

SAMPLE_FOLLOW_UP_USER = [
  "That makes sense, thanks!",
  "Could you show me an example?",
  "What about this specific case?",
  "How would I handle errors?",
  "Is there a more efficient way?",
  "Can you explain that in more detail?",
  "What are the trade-offs?",
  "How do I test this?",
  "What about security concerns?",
  "Thanks, that's exactly what I needed!",
]

SAMPLE_FOLLOW_UP_ASSISTANT = [
  "Here's a complete example with error handling:",
  "Absolutely! Here's how you can handle that specific scenario:",
  "Great point! You should definitely consider input validation:",
  "Yes, there's a more efficient approach using vectorization:",
  "Sure! Let me break this down step by step:",
  "The main trade-offs are performance vs. readability:",
  "For testing, I recommend using pytest with these fixtures:",
  "Good question about security! You should sanitize all inputs:",
  "You're welcome! Feel free to ask if you have more questions.",
  "Let me know if you need help implementing any of these suggestions!",
]

# Sample eChart configurations for chart options
SAMPLE_LINE_CHART_OPTIONS = [
  {
    "title": {"text": "Revenue Trend"},
    "toolbox": {"feature": {"saveAsImage": {}}},
    "xAxis": {"type": "category", "data": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]},
    "yAxis": {"type": "value", "name": "Revenue ($)", "axisLabel": {"formatter": "${value}K"}},
    "tooltip": {
      "trigger": "axis",
      "axisPointer": {"type": "cross", "label": {"backgroundColor": "#6a7985"}},
    },
    "legend": {"data": ["Revenue"]},
    "series": [
      {"name": "Revenue", "data": [150, 230, 224, 218, 135, 147], "type": "line", "smooth": True}
    ],
  },
  {
    "title": {"text": "User Growth"},
    "toolbox": {"feature": {"saveAsImage": {}}},
    "xAxis": {"type": "category", "data": ["Q1", "Q2", "Q3", "Q4"]},
    "yAxis": {"type": "value", "name": "Users", "axisLabel": {"formatter": "{value}"}},
    "tooltip": {
      "trigger": "axis",
      "axisPointer": {"type": "cross", "label": {"backgroundColor": "#6a7985"}},
    },
    "legend": {"data": ["Active Users", "New Users"]},
    "series": [
      {"name": "Active Users", "data": [1200, 1450, 1800, 2100], "type": "line", "smooth": True},
      {"name": "New Users", "data": [200, 350, 420, 480], "type": "line", "smooth": True},
    ],
  },
  {
    "title": {"text": "Stock Price"},
    "toolbox": {"feature": {"saveAsImage": {}}},
    "xAxis": {
      "type": "category",
      "data": ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5", "Week 6", "Week 7", "Week 8"],
    },
    "yAxis": {"type": "value", "name": "Price ($)", "axisLabel": {"formatter": "${value}"}},
    "tooltip": {
      "trigger": "axis",
      "axisPointer": {"type": "cross", "label": {"backgroundColor": "#6a7985"}},
    },
    "legend": {"data": ["AAPL", "GOOGL"]},
    "series": [
      {
        "name": "AAPL",
        "data": [150.5, 152.3, 148.9, 155.7, 159.2, 157.1, 161.4, 163.8],
        "type": "line",
        "smooth": True,
      },
      {
        "name": "GOOGL",
        "data": [2650.2, 2680.5, 2620.1, 2720.8, 2750.3, 2710.6, 2780.9, 2820.4],
        "type": "line",
        "smooth": True,
      },
    ],
  },
  {
    "title": {"text": "Temperature"},
    "toolbox": {"feature": {"saveAsImage": {}}},
    "xAxis": {"type": "category", "data": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]},
    "yAxis": {"type": "value", "name": "Temperature (°F)", "axisLabel": {"formatter": "{value}°F"}},
    "tooltip": {
      "trigger": "axis",
      "axisPointer": {"type": "cross", "label": {"backgroundColor": "#6a7985"}},
    },
    "legend": {"data": ["High", "Low"]},
    "series": [
      {"name": "High", "data": [78, 82, 85, 79, 76, 80, 83], "type": "line", "smooth": True},
      {"name": "Low", "data": [65, 68, 71, 67, 64, 66, 69], "type": "line", "smooth": True},
    ],
  },
]

SAMPLE_BAR_CHART_OPTIONS = [
  {
    "title": {"text": "Sales by Region"},
    "toolbox": {"feature": {"saveAsImage": {}}},
    "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
    "xAxis": {"type": "category", "data": ["North", "South", "East", "West", "Central"]},
    "yAxis": {"type": "value", "name": "Sales ($K)", "axisLabel": {"formatter": "${value}K"}},
    "series": [
      {"name": "Sales", "data": [120, 200, 150, 180, 90], "type": "bar", "barWidth": "60%"}
    ],
  },
  {
    "title": {"text": "Product Performance"},
    "toolbox": {"feature": {"saveAsImage": {}}},
    "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
    "xAxis": {
      "type": "category",
      "data": ["Product A", "Product B", "Product C", "Product D", "Product E"],
    },
    "yAxis": {"type": "value", "name": "Units Sold", "axisLabel": {"formatter": "{value}"}},
    "series": [
      {
        "name": "Units Sold",
        "data": [450, 680, 320, 890, 240],
        "type": "bar",
        "barWidth": "50%",
        "itemStyle": {"color": "#5470c6"},
      }
    ],
  },
  {
    "title": {"text": "Monthly Expenses"},
    "toolbox": {"feature": {"saveAsImage": {}}},
    "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
    "xAxis": {
      "type": "category",
      "data": ["Housing", "Food", "Transport", "Entertainment", "Healthcare", "Utilities"],
    },
    "yAxis": {"type": "value", "name": "Amount ($)", "axisLabel": {"formatter": "${value}"}},
    "series": [
      {
        "name": "Expenses",
        "data": [1200, 800, 400, 300, 250, 200],
        "type": "bar",
        "barWidth": "70%",
        "itemStyle": {"color": "#91cc75"},
      }
    ],
  },
  {
    "title": {"text": "Team Performance"},
    "toolbox": {"feature": {"saveAsImage": {}}},
    "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
    "xAxis": {"type": "category", "data": ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]},
    "yAxis": {"type": "value", "name": "Score", "axisLabel": {"formatter": "{value}"}},
    "series": [
      {
        "name": "Score",
        "data": [85, 92, 78, 96, 88],
        "type": "bar",
        "barWidth": "55%",
        "itemStyle": {"color": "#fac858"},
      }
    ],
  },
  {
    "title": {"text": "Browser Usage"},
    "toolbox": {"feature": {"saveAsImage": {}}},
    "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
    "xAxis": {"type": "category", "data": ["Chrome", "Firefox", "Safari", "Edge", "Opera"]},
    "yAxis": {"type": "value", "name": "Users (%)", "axisLabel": {"formatter": "{value}%"}},
    "series": [
      {
        "name": "Market Share",
        "data": [65.2, 18.8, 9.6, 4.1, 2.3],
        "type": "bar",
        "barWidth": "65%",
        "itemStyle": {"color": "#ee6666"},
      }
    ],
  },
]


def create_mock_conversation(session_id: int, num_exchanges: int = None) -> list[Message]:
  """Create a realistic conversation between user and assistant."""
  if num_exchanges is None:
    num_exchanges = random.randint(2, 8)

  messages = []
  message_id = 1

  # Start with user message
  messages.append(
    Message(
      session_id=session_id,
      id=message_id,
      type=TypeEnum.user,
      content=random.choice(SAMPLE_USER_MESSAGES),
      option=None,
    )
  )
  message_id += 1

  # Add assistant response (may include chart option)
  assistant_msg = create_assistant_message(session_id, message_id)
  messages.append(assistant_msg)
  message_id += 1

  # Add follow-up exchanges
  for _ in range(num_exchanges - 1):
    # User follow-up
    messages.append(
      Message(
        session_id=session_id,
        id=message_id,
        type=TypeEnum.user,
        content=random.choice(SAMPLE_FOLLOW_UP_USER),
        option=None,
      )
    )
    message_id += 1

    # Assistant response (may include chart option)
    assistant_msg = create_assistant_message(session_id, message_id)
    messages.append(assistant_msg)
    message_id += 1

  return messages


def create_assistant_message(
  session_id: int, message_id: int, force_chart: bool = False
) -> Message:
  """Create an assistant message with either content or chart option."""
  # Higher chance for charts (60%), or forced chart
  should_create_chart = force_chart or random.random() < 0.6

  if should_create_chart:
    # Choose between line chart or bar chart
    chart_type = random.choice(["line", "bar"])

    if chart_type == "line":
      chart_option = random.choice(SAMPLE_LINE_CHART_OPTIONS)
    else:
      chart_option = random.choice(SAMPLE_BAR_CHART_OPTIONS)

    return Message(
      session_id=session_id,
      id=message_id,
      type=TypeEnum.assistant,
      content=None,  # Content must be null when option is set
      option=chart_option,
    )
  else:
    # Regular text response
    return Message(
      session_id=session_id,
      id=message_id,
      type=TypeEnum.assistant,
      content=random.choice(SAMPLE_ASSISTANT_MESSAGES),
      option=None,
    )


def create_targeted_conversation(
  session_id: int, num_exchanges: int, chart_heavy: bool
) -> list[Message]:
  """Create a conversation with specific characteristics."""
  messages = []
  message_id = 1

  # Start with user message
  messages.append(
    Message(
      session_id=session_id,
      id=message_id,
      type=TypeEnum.user,
      content=random.choice(SAMPLE_USER_MESSAGES),
      option=None,
    )
  )
  message_id += 1

  # Add exchanges
  for exchange in range(num_exchanges):
    # Assistant response - force chart for chart-heavy sessions on some responses
    force_chart = chart_heavy and (exchange == 1 or (exchange > 2 and random.random() < 0.8))

    assistant_msg = create_assistant_message(session_id, message_id, force_chart)
    messages.append(assistant_msg)
    message_id += 1

    # Add user follow-up (except for last exchange)
    if exchange < num_exchanges - 1:
      messages.append(
        Message(
          session_id=session_id,
          id=message_id,
          type=TypeEnum.user,
          content=random.choice(SAMPLE_FOLLOW_UP_USER),
          option=None,
        )
      )
      message_id += 1

  return messages


def generate_mock_sessions(db: Session, num_sessions: int = 4):
  """Generate mock chat sessions with conversations."""
  print(f"Generating {num_sessions} mock chat sessions...")

  # Base time for realistic timestamps
  base_time = datetime.now() - timedelta(days=30)

  # Specific session configurations
  session_configs = [
    {
      "title": "Financial Dashboard Setup",
      "exchanges": 8,
      "chart_heavy": True,
    },  # ~17 messages (1 user + 8*2), chart-heavy
    {
      "title": "Sales Data Visualization",
      "exchanges": 4,
      "chart_heavy": True,
    },  # ~9 messages (1 user + 4*2), chart-heavy
    {
      "title": "Revenue Trend Analysis",
      "exchanges": 5,
      "chart_heavy": True,
    },  # ~11 messages (1 user + 5*2), chart-heavy
    {
      "title": "Product Performance Review",
      "exchanges": 3,
      "chart_heavy": False,
    },  # ~7 messages (1 user + 3*2), text-heavy
  ]

  for i in range(1, num_sessions + 1):
    # Create session with realistic timestamp
    session_time = base_time + timedelta(
      days=random.randint(0, 30), hours=random.randint(0, 23), minutes=random.randint(0, 59)
    )

    config = session_configs[i - 1] if i <= len(session_configs) else session_configs[0]

    session = ChatSession(
      session_id=i,
      title=config["title"],
      created_at=session_time,
      updated_at=session_time + timedelta(minutes=random.randint(5, 60)),
    )

    db.add(session)
    db.flush()  # Ensure session is created before adding messages

    # Generate conversation for this session
    messages = create_targeted_conversation(i, config["exchanges"], config["chart_heavy"])

    for message in messages:
      db.add(message)

    print(f"✓ Created session {i}: '{session.title}' with {len(messages)} messages")

  db.commit()
  print(f"✅ Successfully created {num_sessions} chat sessions with conversations!")


def clear_existing_data(db: Session):
  """Clear existing data from sessions and messages tables."""
  print("Clearing existing data...")

  # Delete in correct order due to foreign key constraints
  deleted_messages = db.query(Message).delete()
  deleted_sessions = db.query(ChatSession).delete()

  db.commit()

  print(f"✓ Deleted {deleted_messages} messages")
  print(f"✓ Deleted {deleted_sessions} chat sessions")


def seed_database(num_sessions: int = 4, clear_first: bool = True):
  """Main seeding function."""
  print("🌱 Starting database seeding process...")

  # Create database session
  db = SessionLocal()

  try:
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    if clear_first:
      clear_existing_data(db)

    generate_mock_sessions(db, num_sessions)

    # Verify data was created
    session_count = db.query(ChatSession).count()
    message_count = db.query(Message).count()

    print("\n📊 Seeding completed successfully!")
    print(f"   Total sessions: {session_count}")
    print(f"   Total messages: {message_count}")
    print(f"   Average messages per session: {message_count / session_count:.1f}")

  except Exception as e:
    print(f"❌ Error during seeding: {e}")
    db.rollback()
    raise
  finally:
    db.close()


if __name__ == "__main__":
  # Seed with 4 sessions by default
  seed_database(num_sessions=4, clear_first=True)
