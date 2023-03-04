.PHONY: test
test:
	@echo "Starting tests..."
	{ \
		if [ -d "venv" ] ; then	\
			. venv/bin/activate ; \
		fi && \
		noprint -e -f noprint && \
		black --check src tests && \
		pylint -j 0 src tests && \
		pytest --cov-report term-missing --cov=noprint -s -v tests && \
		coverage report --fail-under=100 && \
		echo "Finished"; \
	}
	
.PHONY: format
format:
	{ \
		. venv/bin/activate; \
		black src tests ; \
	}
	