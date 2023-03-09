.PHONY: test
test:
	@echo "Starting tests..."
	# Options for noprint are separately due to older Python 3.7 (automatic testing purposes)
	{ \
		if [ -d "venv" ] ; then	\
			. venv/bin/activate ; \
		fi && \
		noprint -e -f -v -v -m 0 noprint tests && \
		black --check src tests && \
		pytest --cov-report term-missing --cov=noprint -s -v tests && \
		echo "Finished"; \
	}
	#pylint -j 0 src tests && \
	#coverage report --fail-under=100 && \
	
.PHONY: format
format:
	{ \
		. venv/bin/activate; \
		black src tests ; \
	}
	