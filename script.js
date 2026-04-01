const jobs = [
  {
    title: 'Frontend Engineer',
    company: 'NovaTech',
    location: 'Remote',
    skills: ['React', 'TypeScript', 'Accessibility'],
    description: 'Build performant user interfaces and collaborate on design systems.'
  },
  {
    title: 'Data Analyst',
    company: 'Helio Insights',
    location: 'New York, NY',
    skills: ['SQL', 'Python', 'Tableau'],
    description: 'Analyze market trends and generate executive-ready dashboards.'
  },
  {
    title: 'AI Product Manager',
    company: 'Vertex Labs',
    location: 'Austin, TX',
    skills: ['LLMs', 'Roadmaps', 'Experimentation'],
    description: 'Own AI product strategy, experimentation, and cross-team delivery.'
  },
  {
    title: 'Backend Developer',
    company: 'CloudForge',
    location: 'San Francisco, CA',
    skills: ['Node.js', 'API Design', 'PostgreSQL'],
    description: 'Design resilient APIs and improve platform reliability at scale.'
  }
];

const jobResults = document.getElementById('jobResults');
const jobQuery = document.getElementById('jobQuery');
const resumeUpload = document.getElementById('resumeUpload');
const resumeStatus = document.getElementById('resumeStatus');
const jobDescription = document.getElementById('jobDescription');
const atsOutput = document.getElementById('atsOutput');
const applicationsBody = document.getElementById('applicationsBody');

let resumeText = '';

function renderJobs(list) {
  jobResults.innerHTML = '';
  if (!list.length) {
    jobResults.innerHTML = '<li class="job-item">No jobs found for that search.</li>';
    return;
  }

  list.forEach((job) => {
    const li = document.createElement('li');
    li.className = 'job-item';
    li.innerHTML = `
      <strong>${job.title}</strong> — ${job.company}<br />
      <small>${job.location}</small><br />
      <small><em>Skills:</em> ${job.skills.join(', ')}</small>
      <p>${job.description}</p>
    `;
    jobResults.appendChild(li);
  });
}

function searchJobs() {
  const query = jobQuery.value.toLowerCase().trim();
  if (!query) {
    renderJobs(jobs);
    return;
  }

  const filtered = jobs.filter((job) => {
    const haystack = [job.title, job.company, job.location, job.skills.join(' '), job.description]
      .join(' ')
      .toLowerCase();
    return haystack.includes(query);
  });

  renderJobs(filtered);
}

function tokenize(text) {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, ' ')
    .split(/\s+/)
    .filter((word) => word.length > 3);
}

function analyzeATS() {
  const jd = jobDescription.value;
  if (!resumeText) {
    atsOutput.innerHTML = 'Please upload your resume first.';
    return;
  }

  if (!jd.trim()) {
    atsOutput.innerHTML = 'Please paste a job description to compare against your resume.';
    return;
  }

  const jdTokens = [...new Set(tokenize(jd))];
  const resumeTokens = new Set(tokenize(resumeText));

  const matched = jdTokens.filter((word) => resumeTokens.has(word));
  const missing = jdTokens.filter((word) => !resumeTokens.has(word));
  const score = Math.round((matched.length / Math.max(jdTokens.length, 1)) * 100);

  atsOutput.innerHTML = `
    <strong>ATS Match Score:</strong> ${score}%<br />
    <strong>Matched keywords:</strong> ${matched.slice(0, 20).join(', ') || 'None'}<br />
    <strong>Missing keywords to add:</strong> ${missing.slice(0, 20).join(', ') || 'None'}
  `;
}

function renderApplications() {
  const apps = JSON.parse(localStorage.getItem('applications') || '[]');
  applicationsBody.innerHTML = '';

  apps.forEach((app) => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${app.company}</td>
      <td>${app.role}</td>
      <td>${app.status}</td>
      <td>${app.date}</td>
    `;
    applicationsBody.appendChild(row);
  });
}

function addApplication(event) {
  event.preventDefault();

  const newApplication = {
    company: document.getElementById('companyInput').value,
    role: document.getElementById('roleInput').value,
    status: document.getElementById('statusInput').value,
    date: document.getElementById('dateInput').value
  };

  const apps = JSON.parse(localStorage.getItem('applications') || '[]');
  apps.unshift(newApplication);
  localStorage.setItem('applications', JSON.stringify(apps));

  event.target.reset();
  renderApplications();
}

document.getElementById('searchButton').addEventListener('click', searchJobs);
document.getElementById('analyzeButton').addEventListener('click', analyzeATS);
document.getElementById('applicationForm').addEventListener('submit', addApplication);

resumeUpload.addEventListener('change', async (event) => {
  const file = event.target.files[0];
  if (!file) {
    return;
  }

  if (file.type.startsWith('text/') || file.name.endsWith('.md') || file.name.endsWith('.txt')) {
    resumeText = await file.text();
    resumeStatus.textContent = `Uploaded: ${file.name}. Ready for ATS analysis.`;
  } else {
    resumeText = '';
    resumeStatus.textContent = `${file.name} uploaded. For live keyword analysis, upload a .txt or .md resume.`;
  }
});

renderJobs(jobs);
renderApplications();
