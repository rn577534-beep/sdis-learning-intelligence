import os
import secrets
import hashlib

from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from sqlalchemy import select, text, func

from .database import Base, DATABASE_URL, engine, get_db
from .models import Student, AssessmentAttempt, LearningAgentRun
from .schemas import StudentCreate, StudentOut, AttemptCreate
from .curriculum import OBJECTIVES, ASSESSMENTS
from .learning import make_learning_plan
from .agents import AGENT_ROLES, run_learning_agent_team

if DATABASE_URL.startswith("sqlite"):
    # Local development convenience. Production schema is managed in PostgreSQL.
    Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SDIS MVP",
    version="0.1.0",
    description=(
        "Evidence-led student learning support prototype. "
        "Demonstration curriculum and heuristic scoring only."
    ),
)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(api_key: str | None = Depends(api_key_header)):
    expected_key = os.getenv("SDIS_API_KEY")
    if not expected_key:
        raise HTTPException(status_code=503, detail="API access is not configured")
    if not api_key or not secrets.compare_digest(api_key, expected_key):
        raise HTTPException(status_code=401, detail="Valid X-API-Key header required")


def require_teacher_key(api_key: str | None = Depends(api_key_header)):
    """Teacher access key; dedicated key overrides the legacy shared key."""
    expected_key = os.getenv("SDIS_TEACHER_API_KEY") or os.getenv("SDIS_API_KEY")
    if not expected_key:
        raise HTTPException(status_code=503, detail="Teacher API access is not configured")
    if not api_key or not secrets.compare_digest(api_key, expected_key):
        raise HTTPException(status_code=401, detail="Valid teacher API key required")


DASHBOARD_HTML = r"""<!doctype html>
<html lang="bn">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#102b46">
<meta name="description" content="SDIS Learning Intelligence — শিক্ষার্থী শেখার ডেমো ড্যাশবোর্ড">
<title>SDIS — Learning Intelligence</title>
<style>
:root{--ink:#15283e;--muted:#68788d;--blue:#1768e5;--mint:#d9f6e9;--line:#e6edf4;--paper:#f5f8fc;--white:#fff;--orange:#ffbd69}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:ui-sans-serif,system-ui,-apple-system,"Noto Sans Bengali","Segoe UI",sans-serif;line-height:1.55}a{color:inherit}.shell{max-width:1160px;margin:auto;padding:0 22px}.top{background:#102b46;color:white;padding:16px 0}.toprow{display:flex;align-items:center;justify-content:space-between;gap:14px}.brand{display:flex;gap:12px;align-items:center;font-weight:800;letter-spacing:.2px}.logo{display:grid;place-items:center;background:#c8f5df;color:#123c36;width:42px;height:42px;border-radius:14px;font-size:20px}.brand small{display:block;color:#b9ccdf;font-size:11px;font-weight:500;letter-spacing:1.3px}.links{display:flex;gap:16px;flex-wrap:wrap;font-size:13px;color:#d6e5f4}.links a{text-decoration:none}.links a:hover{text-decoration:underline}.hero{padding:36px 0 24px;display:grid;grid-template-columns:1.4fr .8fr;gap:22px;align-items:stretch}.eyebrow{color:var(--blue);font-size:12px;font-weight:800;letter-spacing:1.3px;text-transform:uppercase}.hero h1{font-size:clamp(30px,4vw,46px);line-height:1.14;margin:10px 0 14px;letter-spacing:-1.2px}.hero p{max-width:620px;color:var(--muted);margin:0}.heroCard{border-radius:24px;background:linear-gradient(135deg,#1768e5,#0c4db8);color:white;padding:24px;position:relative;overflow:hidden;min-height:190px}.heroCard:after{content:"";position:absolute;width:170px;height:170px;border:28px solid #ffffff20;border-radius:50%;right:-45px;bottom:-80px}.heroCard .pill{background:#ffffff20;color:white}.heroCard h2{font-size:23px;margin:18px 0 6px;position:relative;z-index:1}.heroCard p{color:#e0ecff;font-size:14px;position:relative;z-index:1}.pill{display:inline-flex;align-items:center;gap:7px;background:#eaf2ff;color:#1655b4;border-radius:999px;padding:6px 11px;font-size:12px;font-weight:750}.dot{width:7px;height:7px;border-radius:50%;background:#27bd82}.warning{border:1px solid #f1d9a7;background:#fff8e9;color:#75531b;border-radius:13px;padding:12px 15px;font-size:13px;margin:0 0 22px}.sectionHead{display:flex;justify-content:space-between;align-items:end;gap:12px;margin:28px 0 14px}.sectionHead h2{margin:0;font-size:21px}.sectionHead p{margin:4px 0 0;color:var(--muted);font-size:13px}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:15px}.card{background:white;border:1px solid var(--line);border-radius:18px;padding:20px;box-shadow:0 4px 16px #203b5708}.stat{display:flex;align-items:center;gap:13px}.icon{width:44px;height:44px;border-radius:13px;display:grid;place-items:center;font-size:20px;background:#edf4ff}.stat strong{display:block;font-size:19px}.stat span{font-size:12px;color:var(--muted)}.assessment{display:grid;grid-template-columns:1.3fr .7fr;gap:16px;margin-top:16px}.assessmentMain{background:white;border:1px solid var(--line);border-radius:22px;padding:24px}.assessmentMain h3{font-size:22px;margin:12px 0 5px}.meta{display:flex;gap:8px;flex-wrap:wrap;color:var(--muted);font-size:12px;margin:12px 0 18px}.meta span{background:#f2f5f9;border-radius:8px;padding:5px 9px}.btn{border:0;border-radius:12px;padding:12px 17px;font:inherit;font-weight:750;cursor:pointer;transition:transform .15s,background .15s}.btn:hover{transform:translateY(-1px)}.primary{background:var(--blue);color:white}.secondary{background:#eaf2ff;color:#1655b4}.outline{background:white;border:1px solid var(--line);color:var(--ink)}.sideNote{border-radius:22px;padding:22px;background:#e9f8f1;border:1px solid #d5f0e3}.sideNote h3{margin:0 0 8px;font-size:17px}.sideNote p,.sideNote li{font-size:13px;color:#416b5a}.sideNote ul{padding-left:18px}.quiz{display:none;margin-top:20px}.quiz.active{display:block}.progressLine{height:7px;background:#eaf0f7;border-radius:20px;overflow:hidden;margin:12px 0 22px}.progressLine span{display:block;height:100%;width:0;background:#24a878;transition:width .2s}.question{padding:18px 0;border-top:1px solid var(--line)}.question:first-of-type{border-top:0}.question h4{margin:0 0 12px;font-size:17px}.qnum{color:var(--blue);font-size:12px;font-weight:800;letter-spacing:.5px}.options{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}.option{display:flex;align-items:center;gap:9px;border:1px solid #dce5ef;padding:12px;border-radius:12px;cursor:pointer;background:white}.option:has(input:checked){border-color:var(--blue);background:#eff5ff}.option input{accent-color:var(--blue)}.quizActions{display:flex;gap:10px;flex-wrap:wrap;margin-top:16px}.result{display:none;margin-top:18px}.result.active{display:block}.scorePanel{background:#102b46;color:white;border-radius:18px;padding:23px;display:flex;align-items:center;gap:22px;flex-wrap:wrap}.scoreNum{font-size:40px;font-weight:850;line-height:1}.scorePanel p{margin:6px 0 0;color:#c9d9e9;font-size:13px}.reviewList{display:grid;gap:12px;margin-top:15px}.reviewItem{background:white;border:1px solid var(--line);border-radius:15px;padding:17px}.reviewItem h4{margin:0 0 8px}.tag{display:inline-block;border-radius:7px;padding:3px 8px;font-size:11px;font-weight:800;margin-bottom:8px}.correct{background:#dcf8eb;color:#126d49}.incorrect{background:#fff0db;color:#8b4d0b}.reviewItem p{font-size:13px;margin:6px 0;color:var(--muted)}.plan{background:#eff5ff;border:1px solid #dce9ff;padding:18px;border-radius:15px;margin-top:15px}.plan h3{margin:0 0 8px;font-size:17px}.plan li{margin:6px 0;font-size:13px}.foot{margin-top:34px;background:#102b46;color:#c3d3e4;padding:22px 0;font-size:12px}.footrow{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}.foot a{color:white}.sr{position:absolute;left:-9999px}@media(max-width:760px){.hero,.assessment{grid-template-columns:1fr}.grid{grid-template-columns:1fr}.toprow{align-items:flex-start;flex-direction:column}.hero{padding-top:26px}.assessmentMain{padding:18px}.options{grid-template-columns:1fr}.shell{padding:0 15px}.sectionHead{align-items:flex-start;flex-direction:column}}
</style>
</head>
<body>
<header class="top"><div class="shell toprow">
<div class="brand"><div class="logo">S</div><div>SDIS <small>LEARNING INTELLIGENCE</small></div></div>
<nav class="links" aria-label="প্রধান লিংক"><a href="#assessment">ডেমো পরীক্ষা</a><a href="#review">রিভিউ</a><a href="/docs">API ডকস</a><a href="/health/ready">সিস্টেম স্ট্যাটাস</a></nav>
</div></header>
<main class="shell">
<section class="hero"><div><div class="eyebrow">শেখা বুঝে এগিয়ে চলা</div><h1>প্রতিটি শিক্ষার্থীর<br>পরবর্তী শেখার ধাপ।</h1><p>SDIS শেখার অগ্রগতি বুঝতে এবং অনুশীলনের পরবর্তী ধাপ খুঁজে পেতে তৈরি একটি প্রাথমিক ডেমো। ছোট একটি গণিত পরীক্ষা দিয়ে শুরু করুন।</p></div>
<div class="heroCard"><span class="pill"><span class="dot"></span> ডেমো সিস্টেম সচল</span><h2>শুধু নম্বর নয়—<br>শেখার দিকনির্দেশনা</h2><p>উত্তর দেখুন, ব্যাখ্যা পড়ুন, তারপর অনুশীলন করুন।</p></div></section>
<div class="warning"><strong>ডেমো সতর্কতা:</strong> এই প্রশ্ন ও স্কোরিং পদ্ধতি পরীক্ষামূলক; সরকারি পাঠ্যক্রম বা যাচাইকৃত মূল্যায়ন নয়। এই ডেমোতে নাম/ইমেইল নেওয়া হয় না। ফলাফল বেনামী ডেমো রেকর্ড হিসেবে সংরক্ষিত হবে।</div>
<section><div class="sectionHead"><div><h2>আপনার শেখার জায়গা</h2><p>বর্তমানে সক্রিয় ফিচার ও সিস্টেমের সংক্ষিপ্ত অবস্থা</p></div></div>
<div class="grid">
<div class="card stat"><div class="icon">🧩</div><div><strong>৩টি প্রশ্ন</strong><span>ষষ্ঠ শ্রেণির গণিত ডেমো</span></div></div>
<div class="card stat"><div class="icon">📈</div><div><strong>তাৎক্ষণিক রিভিউ</strong><span>উত্তর ও ব্যাখ্যা একসঙ্গে</span></div></div>
<div class="card stat"><div class="icon">🛡️</div><div><strong>গোপনীয়তা-সচেতন</strong><span>এই ডেমোতে নাম লাগবে না</span></div></div>
</div></section>
<section id="assessment"><div class="sectionHead"><div><h2>শুরু করুন</h2><p>প্রায় ২ মিনিট • ৩টি প্রশ্ন • শেষে উত্তর পর্যালোচনা</p></div></div>
<div class="assessment"><div class="assessmentMain"><span class="pill">ষষ্ঠ শ্রেণি · গণিত</span><h3>গণিত দক্ষতা যাচাই</h3><p style="color:var(--muted);margin:0">যোগ, গুণ ও ভগ্নাংশের একটি প্রাথমিক ধারণা যাচাই করুন। প্রতিটি প্রশ্নে একটি উত্তর বেছে নিন।</p><div class="meta"><span>৩ নম্বর</span><span>সময়সীমা নেই</span><span>নমুনা প্রশ্ন</span></div>
<button class="btn primary" id="startBtn">পরীক্ষা শুরু করুন →</button>
<div class="quiz" id="quiz"><div style="display:flex;justify-content:space-between;gap:10px;font-size:12px;color:var(--muted)"><span id="progressText">প্রশ্ন ১ / ৩</span><span>অগ্রগতি</span></div><div class="progressLine"><span id="progressBar"></span></div>
<form id="quizForm">
<div class="question"><div class="qnum">প্রশ্ন ০১</div><h4>৭ + ৫ = কত?</h4><div class="options"><label class="option"><input type="radio" name="q1" value="10"> ১০</label><label class="option"><input type="radio" name="q1" value="12"> ১২</label><label class="option"><input type="radio" name="q1" value="13"> ১৩</label><label class="option"><input type="radio" name="q1" value="14"> ১৪</label></div></div>
<div class="question"><div class="qnum">প্রশ্ন ০২</div><h4>৩ × ৫ = কত?</h4><div class="options"><label class="option"><input type="radio" name="q2" value="8"> ৮</label><label class="option"><input type="radio" name="q2" value="12"> ১২</label><label class="option"><input type="radio" name="q2" value="15"> ১৫</label><label class="option"><input type="radio" name="q2" value="20"> ২০</label></div></div>
<div class="question"><div class="qnum">প্রশ্ন ০৩</div><h4>একটি সম্পূর্ণ জিনিসকে ৪টি সমান ভাগ করা হলো। এর মধ্যে ২টি ভাগ চিহ্নিত। কয়টি ভাগ চিহ্নিত?</h4><div class="options"><label class="option"><input type="radio" name="q3" value="1"> ১টি</label><label class="option"><input type="radio" name="q3" value="2"> ২টি</label><label class="option"><input type="radio" name="q3" value="3"> ৩টি</label><label class="option"><input type="radio" name="q3" value="4"> ৪টি</label></div></div>
<div class="quizActions"><button class="btn primary" type="submit">উত্তর জমা দিয়ে রিভিউ দেখুন</button><button class="btn outline" type="button" id="cancelBtn">বন্ধ করুন</button></div><p id="formError" style="display:none;color:#a53b30;font-size:13px" role="alert">রিভিউ দেখার আগে তিনটি প্রশ্নেরই উত্তর দিন।</p>
</form></div>
<div class="result" id="result" aria-live="polite"></div>
</div><aside class="sideNote"><h3>এই ডেমো কী দেখাবে?</h3><ul><li>মোট স্কোর ও শতকরা ফল</li><li>প্রতিটি উত্তরের সঠিক উত্তর</li><li>সংক্ষিপ্ত ব্যাখ্যা</li><li>আরও অনুশীলনের প্রস্তাব</li></ul><p><strong>মনে রাখুন:</strong> একটি ছোট পরীক্ষা দিয়ে কারও সামগ্রিক শেখার ক্ষমতা নির্ধারণ করা যায় না।</p></aside></div></section>
<section id="review"><div class="sectionHead"><div><h2>রিভিউ ও পরবর্তী ধাপ</h2><p>পরীক্ষা শেষ করলে আপনার ফলাফল এই অংশে দেখা যাবে।</p></div></div><div class="card" id="reviewPlaceholder" style="color:var(--muted)">এখনও কোনো উত্তর জমা হয়নি। উপরের ডেমো পরীক্ষা শেষ করলে বিস্তারিত রিভিউ এখানে খুলবে।</div></section>
</main>
<footer class="foot"><div class="shell footrow"><span>© SDIS Learning Intelligence · প্রাথমিক প্রোটোটাইপ</span><span><a href="/docs">API ডকস</a> · <a href="/health">Health</a> · <a href="/health/ready">Database status</a></span></div></footer>
<script>
const questions=[
 {id:"q1",answer:"12",title:"৭ + ৫ = কত?",explain:"৭-এর সঙ্গে ৫ যোগ করলে ১২ হয়। চাইলে ৭ থেকে শুরু করে আরও পাঁচ ধাপ গুনে যাচাই করুন।",topic:"পূর্ণসংখ্যার যোগ"},
 {id:"q2",answer:"15",title:"৩ × ৫ = কত?",explain:"৩ × ৫ মানে ৫-কে তিনবার যোগ করা: ৫ + ৫ + ৫ = ১৫।",topic:"গুণ"},
 {id:"q3",answer:"2",title:"কয়টি ভাগ চিহ্নিত?",explain:"প্রশ্নে বলা হয়েছে চারটি সমান ভাগের মধ্যে দুটি চিহ্নিত। তাই উত্তর ২টি। পুরো অংশকে চার ভাগ করলে চিহ্নিত অংশ ২/৪ বা অর্ধেক।",topic:"ভগ্নাংশের প্রাথমিক ধারণা"}
];
const startBtn=document.getElementById("startBtn"),quiz=document.getElementById("quiz"),result=document.getElementById("result"),form=document.getElementById("quizForm");
startBtn.addEventListener("click",()=>{quiz.classList.add("active");result.classList.remove("active");startBtn.style.display="none";document.getElementById("reviewPlaceholder").style.display="block";quiz.scrollIntoView({behavior:"smooth",block:"start"});});
document.getElementById("cancelBtn").addEventListener("click",()=>{quiz.classList.remove("active");startBtn.style.display="inline-block";});
form.addEventListener("change",()=>{const answered=questions.filter(q=>form.querySelector('input[name="'+q.id+'"]:checked')).length;document.getElementById("progressText").textContent="উত্তর দেওয়া হয়েছে "+answered+" / 3";document.getElementById("progressBar").style.width=(answered/3*100)+"%";document.getElementById("formError").style.display="none";});
form.addEventListener("submit",async e=>{e.preventDefault();const answers={};questions.forEach(q=>{const el=form.querySelector('input[name="'+q.id+'"]:checked');if(el)answers[q.id]=el.value;});if(Object.keys(answers).length!==3){document.getElementById("formError").style.display="block";return;}const submitBtn=form.querySelector('button[type="submit"]');submitBtn.disabled=true;submitBtn.textContent="ফলাফল সংরক্ষণ হচ্ছে…";let serverResult;try{const response=await fetch("/demo/attempts",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({student_id:1,demo_session_id:(()=>{let id=localStorage.getItem("sdis_demo_session");if(!id){id=crypto.randomUUID().replace(/-/g,"");localStorage.setItem("sdis_demo_session",id)}return id})(),answers:questions.map(q=>({question_id:q.id,answer:answers[q.id]}))})});if(!response.ok)throw new Error("API response "+response.status);serverResult=await response.json();}catch(err){document.getElementById("formError").textContent="ফলাফল সার্ভারে সংরক্ষণ করা যায়নি। সংযোগ পরীক্ষা করে আবার চেষ্টা করুন।";document.getElementById("formError").style.display="block";submitBtn.disabled=false;submitBtn.textContent="আবার জমা দিন";return;}submitBtn.disabled=false;submitBtn.textContent="উত্তর জমা দিয়ে রিভিউ দেখুন";const score=serverResult.score;const percent=serverResult.percent;const agentSummary='<div class="plan"><h3>🤖 শেখার এজেন্ট টিম</h3><p style="font-size:13px">৬টি এজেন্ট আপনার উত্তর ও বিষয়ভিত্তিক অগ্রগতি বিশ্লেষণ করেছে। এটি প্রাথমিক নিয়মভিত্তিক বিশ্লেষণ, চূড়ান্ত মূল্যায়ন নয়।</p><ul>'+serverResult.agent_team.recommendations.map(r=>'<li>'+r.action+'</li>').join('')+'</ul><p style="font-size:12px;color:var(--muted)">একই ব্রাউজারে পুনরায় পরীক্ষা দিলে আপনার বেনামী অগ্রগতির রেকর্ড যুক্ত হবে।</p></div>';const details=questions.map((q,i)=>{const ok=answers[q.id]===q.answer;return '<article class="reviewItem"><span class="tag '+(ok?'correct':'incorrect')+'">'+(ok?'✓ সঠিক উত্তর':'↻ আবার অনুশীলন করুন')+'</span><h4>'+(i+1)+'. '+q.title+'</h4><p><strong>আপনার উত্তর:</strong> '+answers[q.id]+'</p><p><strong>সঠিক উত্তর:</strong> '+q.answer+'</p><p>'+q.explain+'</p><p><strong>বিষয়:</strong> '+q.topic+'</p></article>';}).join("");const weak=questions.filter(q=>answers[q.id]!==q.answer);const plan=weak.length?'<div class="plan"><h3>📚 পরবর্তী অনুশীলন</h3><p style="font-size:13px;color:var(--muted)">যে বিষয়গুলোতে ভুল হয়েছে, সেগুলো দিয়ে শুরু করুন:</p><ul>'+weak.map(q=>'<li><strong>'+q.topic+'</strong> — একটি উদাহরণ দেখে একই ধরনের ৩টি অঙ্ক অনুশীলন করুন।</li>').join("")+'</ul><p style="font-size:12px;color:var(--muted)">প্রয়োজনে শিক্ষক/অভিভাবকের সঙ্গে উত্তরগুলো মিলিয়ে নিন।</p></div>':'<div class="plan"><h3>🌱 এবার একটু এগিয়ে যান</h3><p style="font-size:13px">সবগুলো ডেমো প্রশ্ন সঠিক হয়েছে। এবার একটু কঠিন অঙ্ক অনুশীলন করুন এবং কীভাবে সমাধান করেছেন তা ব্যাখ্যা করার চেষ্টা করুন।</p></div>';result.innerHTML='<div class="scorePanel"><div class="scoreNum">'+score+'/3</div><div><strong style="font-size:20px">আপনার ডেমো ফলাফল: '+percent+'%</strong><p>সার্ভার রেকর্ড #'+serverResult.attempt_id+' · এটি ৩টি নমুনা প্রশ্নের ফল, সামগ্রিক দক্ষতার পরিমাপ নয়।</p></div></div>'+agentSummary+'<div class="reviewList">'+details+'</div>'+plan+'<div class="quizActions"><button class="btn primary" id="retryBtn">আবার চেষ্টা করুন</button><a class="btn outline" href="/docs" style="text-decoration:none">API ডকস দেখুন</a></div>';result.classList.add("active");quiz.classList.remove("active");document.getElementById("reviewPlaceholder").style.display="none";result.scrollIntoView({behavior:"smooth",block:"start"});document.getElementById("retryBtn").addEventListener("click",()=>{form.reset();result.classList.remove("active");quiz.classList.add("active");document.getElementById("progressText").textContent="প্রশ্ন ১ / ৩";document.getElementById("progressBar").style.width="0";quiz.scrollIntoView({behavior:"smooth",block:"start"});});});
</script>
</body></html>"""


@app.get("/", response_class=HTMLResponse)
def root():
    return HTMLResponse(content=DASHBOARD_HTML)


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0", "mode": "prototype"}


@app.get("/health/ready")
def readiness():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception:
        raise HTTPException(status_code=503, detail="Database unavailable")


@app.get("/curriculum/objectives")
def list_objectives(grade_level: str | None = None, subject: str | None = None):
    rows = OBJECTIVES
    if grade_level:
        rows = [item for item in rows if item["grade_level"].lower() == grade_level.lower()]
    if subject:
        rows = [item for item in rows if item["subject"].lower() == subject.lower()]
    return {
        "count": len(rows),
        "objectives": rows,
        "warning": "Demonstration data; not official NCTB content.",
    }


@app.post("/students", response_model=StudentOut, status_code=201, dependencies=[Depends(require_api_key)])
def create_student(payload: StudentCreate, db: Session = Depends(get_db)):
    student = Student(
        display_name=payload.display_name,
        grade_level=payload.grade_level,
        preferred_language=payload.preferred_language,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@app.get("/students/{student_id}", response_model=StudentOut, dependencies=[Depends(require_api_key)])
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@app.get("/assessments/{assessment_id}")
def get_assessment(assessment_id: str):
    assessment = ASSESSMENTS.get(assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    # Never return answer keys to the client.
    return {
        key: value for key, value in assessment.items() if key != "questions"
    } | {
        "questions": [
            {key: value for key, value in question.items() if key != "answer"}
            for question in assessment["questions"]
        ],
        "warning": "Demonstration assessment; not validated.",
    }


@app.post("/assessments/{assessment_id}/attempts", status_code=201, dependencies=[Depends(require_api_key)])
def submit_attempt(assessment_id: str, payload: AttemptCreate, db: Session = Depends(get_db)):
    assessment = ASSESSMENTS.get(assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    student = db.get(Student, payload.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    valid_question_ids = {question["question_id"] for question in assessment["questions"]}
    submitted_ids = {answer.question_id for answer in payload.answers}
    unknown_ids = submitted_ids - valid_question_ids
    if unknown_ids:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Submission contains question IDs not in this assessment",
                "unknown_question_ids": sorted(unknown_ids),
            },
        )

    submitted = {answer.question_id: answer.answer.strip() for answer in payload.answers}
    objective_points = {}
    total_score = 0.0
    max_score = 0.0

    for question in assessment["questions"]:
        points = float(question["points"])
        max_score += points
        objective_id = question["objective_id"]
        objective_points.setdefault(objective_id, {"score": 0.0, "max_score": 0.0})
        objective_points[objective_id]["max_score"] += points
        user_answer = submitted.get(question["question_id"], "")
        # Exact matching is a placeholder, not a validated assessment method.
        if user_answer.casefold() == question["answer"].casefold():
            total_score += points
            objective_points[objective_id]["score"] += points

    objective_results = {}
    for objective_id, values in objective_points.items():
        max_objective_score = values["max_score"]
        percent = round(100 * values["score"] / max_objective_score, 1) if max_objective_score else 0
        objective_results[objective_id] = {
            "score": values["score"],
            "max_score": max_objective_score,
            "percent": percent,
        }

    attempt = AssessmentAttempt(
        student_id=student.id,
        assessment_id=assessment_id,
        answers=[answer.model_dump() for answer in payload.answers],
        score=total_score,
        max_score=max_score,
        objective_results=objective_results,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    percent = round(100 * total_score / max_score, 1) if max_score else 0
    return {
        "attempt_id": attempt.id,
        "student_id": student.id,
        "assessment_id": assessment_id,
        "score": total_score,
        "max_score": max_score,
        "percent": percent,
        "objective_results": objective_results,
        "note": (
            "Prototype rule-based result only. Review with a teacher; "
            "not a diagnosis or permanent label."
        ),
    }


@app.post("/demo/attempts", status_code=201)
def submit_anonymous_demo_attempt(payload: AttemptCreate, db: Session = Depends(get_db)):
    """Pseudonymous demo session; no name, email, or login is required."""
    assessment_id = "demo-math"
    assessment = ASSESSMENTS[assessment_id]
    valid_ids = {q["question_id"] for q in assessment["questions"]}
    submitted = {a.question_id: a.model_dump() for a in payload.answers}
    unknown = set(submitted) - valid_ids
    if unknown:
        raise HTTPException(status_code=422, detail={"message": "Unknown question IDs", "unknown_question_ids": sorted(unknown)})
    session_hash = hashlib.sha256(payload.demo_session_id.encode("utf-8")).hexdigest() if payload.demo_session_id else None
    student = db.scalar(select(Student).where(Student.demo_session_hash == session_hash)) if session_hash else None
    if student is None:
        student = Student(display_name="Anonymous demo learner", grade_level="Grade 6", preferred_language="bn", demo_session_hash=session_hash)
        db.add(student)
        db.flush()
    objective_points, total_score, max_score = {}, 0.0, 0.0
    for question in assessment["questions"]:
        points = float(question["points"]); max_score += points
        oid = question["objective_id"]
        objective_points.setdefault(oid, {"score": 0.0, "max_score": 0.0})
        objective_points[oid]["max_score"] += points
        if submitted.get(question["question_id"], {}).get("answer", "").strip().casefold() == question["answer"].casefold():
            total_score += points; objective_points[oid]["score"] += points
    results = {k: {"score": v["score"], "max_score": v["max_score"], "percent": round(100*v["score"]/v["max_score"], 1) if v["max_score"] else 0} for k,v in objective_points.items()}
    attempt = AssessmentAttempt(student_id=student.id, assessment_id=assessment_id, answers=[a.model_dump() for a in payload.answers], score=total_score, max_score=max_score, objective_results=results)
    db.add(attempt); db.flush()
    recent = list(db.scalars(select(AssessmentAttempt).where(AssessmentAttempt.student_id == student.id, AssessmentAttempt.id != attempt.id).order_by(AssessmentAttempt.created_at.desc(), AssessmentAttempt.id.desc()).limit(4)))
    agent_team = run_learning_agent_team(student.id, attempt, assessment, [a.model_dump() for a in payload.answers], list(reversed(recent)))
    db.add(LearningAgentRun(student_id=student.id, attempt_id=attempt.id, agent_results=agent_team))
    db.commit(); db.refresh(attempt)
    return {"attempt_id":attempt.id,"student_id":student.id,"assessment_id":assessment_id,"score":total_score,"max_score":max_score,"percent":round(100*total_score/max_score,1) if max_score else 0,"objective_results":results,"learning_plan":make_learning_plan(student.id,attempt),"agent_team":agent_team,"note":"Pseudonymous demo record; rule-based prototype only; teacher review required."}

@app.get("/students/{student_id}/learning-plan", dependencies=[Depends(require_api_key)])
def get_learning_plan(student_id: int, db: Session = Depends(get_db)):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    latest = db.scalar(
        select(AssessmentAttempt)
        .where(AssessmentAttempt.student_id == student_id)
        .order_by(AssessmentAttempt.created_at.desc(), AssessmentAttempt.id.desc())
        .limit(1)
    )
    return make_learning_plan(student_id, latest)


@app.get("/students/{student_id}/report", dependencies=[Depends(require_api_key)])
def get_student_report(student_id: int, db: Session = Depends(get_db)):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    attempts = list(db.scalars(
        select(AssessmentAttempt)
        .where(AssessmentAttempt.student_id == student_id)
        .order_by(AssessmentAttempt.created_at.asc(), AssessmentAttempt.id.asc())
    ))
    history = [
        {
            "attempt_id": attempt.id,
            "assessment_id": attempt.assessment_id,
            "score": attempt.score,
            "max_score": attempt.max_score,
            "percent": round(100 * attempt.score / attempt.max_score, 1) if attempt.max_score else 0,
            "created_at": attempt.created_at.isoformat(),
        }
        for attempt in attempts
    ]

    return {
        "student": {
            "id": student.id,
            "display_name": student.display_name,
            "grade_level": student.grade_level,
            "preferred_language": student.preferred_language,
        },
        "attempt_count": len(history),
        "assessment_history": history,
        "latest_objective_results": attempts[-1].objective_results if attempts else {},
        "limitations": [
            "Demo curriculum and assessment are not official or validated.",
            "Scores are limited evidence and must not be used for high-stakes decisions.",
            "Teacher review is required before acting on the suggested learning plan.",
        ],
    }


@app.get("/students/{student_id}/attempts", dependencies=[Depends(require_api_key)])
def get_student_attempt_history(student_id: int, db: Session = Depends(get_db)):
    """Return a student's chronological attempt history without raw answers."""
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    attempts = list(db.scalars(
        select(AssessmentAttempt)
        .where(AssessmentAttempt.student_id == student_id)
        .order_by(AssessmentAttempt.created_at.asc(), AssessmentAttempt.id.asc())
    ))
    return {
        "student_id": student_id,
        "attempt_count": len(attempts),
        "history": [
            {
                "attempt_id": item.id,
                "assessment_id": item.assessment_id,
                "score": item.score,
                "max_score": item.max_score,
                "percent": round(100 * item.score / item.max_score, 1) if item.max_score else 0,
                "objective_results": item.objective_results,
                "created_at": item.created_at.isoformat(),
            }
            for item in attempts
        ],
    }


@app.get("/teacher/dashboard", dependencies=[Depends(require_teacher_key)])
def get_teacher_dashboard(db: Session = Depends(get_db)):
    """Small teacher overview; protected by a teacher-specific key when configured."""
    student_count = db.scalar(select(func.count()).select_from(Student)) or 0
    attempt_count = db.scalar(select(func.count()).select_from(AssessmentAttempt)) or 0
    average_percent = db.scalar(
        select(func.avg(AssessmentAttempt.score / AssessmentAttempt.max_score * 100))
        .where(AssessmentAttempt.max_score > 0)
    )
    recent_rows = db.execute(
        select(AssessmentAttempt, Student.display_name)
        .join(Student, Student.id == AssessmentAttempt.student_id)
        .order_by(AssessmentAttempt.created_at.desc(), AssessmentAttempt.id.desc())
        .limit(10)
    ).all()
    return {
        "project": "SDIS Learning Intelligence",
        "status": "prototype",
        "summary": {
            "student_records": student_count,
            "assessment_attempts": attempt_count,
            "average_score_percent": round(float(average_percent), 1) if average_percent is not None else None,
        },
        "recent_attempts": [
            {
                "attempt_id": attempt.id,
                "student_id": attempt.student_id,
                "student_label": display_name,
                "assessment_id": attempt.assessment_id,
                "score": attempt.score,
                "max_score": attempt.max_score,
                "percent": round(100 * attempt.score / attempt.max_score, 1) if attempt.max_score else 0,
                "created_at": attempt.created_at.isoformat(),
            }
            for attempt, display_name in recent_rows
        ],
        "limitations": [
            "Prototype data and scoring only; not a validated assessment.",
            "Teacher review is required; do not use scores for high-stakes decisions.",
        ],
    }


@app.get("/students/{student_id}/agent-profile", dependencies=[Depends(require_api_key)])
def get_student_agent_profile(student_id: int, db: Session = Depends(get_db)):
    if not db.get(Student, student_id):
        raise HTTPException(status_code=404, detail="Student not found")
    runs = list(db.scalars(select(LearningAgentRun).where(LearningAgentRun.student_id == student_id).order_by(LearningAgentRun.created_at.desc(), LearningAgentRun.id.desc()).limit(10)))
    return {"student_id":student_id,"agent_team":AGENT_ROLES,"runs":[{"attempt_id":r.attempt_id,"created_at":r.created_at.isoformat(),"analysis":r.agent_results} for r in runs],"note":"Evidence-limited prototype. Teacher review required; not a diagnosis or high-stakes assessment."}
