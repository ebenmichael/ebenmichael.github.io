# Local helpers. Deploys happen on GitHub: pushing to master builds the site with Actions.
.PHONY: serve build paper published cv

serve:
	bundle exec jekyll serve --livereload

build:
	bundle exec jekyll build

# make paper ARXIV=2607.14346 [TOPICS=policy-learning,ai-llms]
# make paper DOI=10.1002/sim.70720
paper:
	python3 scripts/add_paper.py $(if $(ARXIV),--arxiv $(ARXIV)) $(if $(DOI),--doi $(DOI)) $(if $(TOPICS),--topics $(TOPICS))

# make published ID=<paper id> DOI=10.xxxx/yyyy [URL=https://journal/link]
published:
	python3 scripts/add_paper.py --published $(ID) --doi $(DOI) $(if $(URL),--url $(URL))

# copy the latest compiled CV into the site
cv:
	cp ~/jobs/resume/ebm_cv.pdf assets/pdfs/cv.pdf
