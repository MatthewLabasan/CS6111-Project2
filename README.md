# CS6111-Project2
## Getting Started

### Prerequisites
1. Python 3.8.1 or higher
2. Install `wget` using `brew install wget`
  - Make sure to restart your terminal after this installation.
3. Google Custom Search Engine API Key
4. Google Search Engine Key
5. Google Gemini 2.0 Flash model (free tier) API Key

### Installation
1. Install requirements.txt
2. Install trained SpanBERT
  The SpanBERT classifier to extract the following four types of relations from text documents:
  - Schools_Attended (internal name: per:schools_attended)
  - Work_For (internal name: per:employee_of)
  - Live_In (internal name: per:cities_of_residence)
  - Top_Member_Employees (internal name: org:top_members/employees)
  There has been  implemented the scripts for downloading and running the pre-trained SpanBERT classifier for the purpose of this project:
  `git clone https://github.com/Shreyas200188/SpanBERT`
  `cd SpanBERT`
  `pip3 install -r requirements.txt`
  `bash download_finetuned.sh`
  Make sure that you work inside the above SpanBERT folder, to have all needed files and dependencies.


Note: This repository is built on Python 3.11.5. The Google Console is in Python 3.8.1. When setting up on the console, may need to downgrade versions in `requirements.txt`. Account for this before submission.