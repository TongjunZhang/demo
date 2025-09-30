FROM nexus.crowncastle.com:8843/base-image-aws-glue-libs-5:latest AS base
ENV AWS_REGION=us-east-2
ENV AWS_ACCESS_KEY_ID=dummy
ENV AWS_SECRET_ACCESS_KEY=dummy
ENV DISABLE_SSL=true
RUN ["mkdir", "-m", "777", "-p", "/home/glue_user/workspace/volume"]
RUN ["chmod", "-R", "777", "/home/glue_user/workspace/volume"]
COPY ./requirements.txt requirements.txt
RUN pip3 install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --no-cache-dir --upgrade -r requirements.txt
COPY tasks /home/glue_user/workspace/tasks/
COPY ./setup.py  /home/glue_user/workspace/setup.py
COPY ./README.md /home/glue_user/workspace/README.md
COPY copy-volume.sh /home/glue_user/workspace/
USER root
RUN ["chmod", "+x", "/home/glue_user/workspace/copy-volume.sh"]
USER glue_user

FROM base as test-local
COPY ./tests /home/glue_user/workspace/tests/
COPY ./requirements-test.txt requirements-test.txt
RUN pip3 install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --no-cache-dir --upgrade -r requirements-test.txt
WORKDIR /home/glue_user/workspace/tests
ENTRYPOINT ["bash"]
# testing 
# TEST:
FROM base as test
COPY ./tasks /home/glue_user/workspace/tasks/
COPY ./tests /home/glue_user/workspace/tests/
COPY ./requirements-test.txt requirements-test.txt
RUN pip3 install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --no-cache-dir --upgrade -r requirements-test.txt
RUN python3 -m pytest /home/glue_user/workspace/tests/ --doctest-modules --junitxml=/home/glue_user/workspace/volume/junit/test-results.xml --cov=/home/glue_user/workspace/tasks --cov-report=xml:/home/glue_user/workspace/volume/coverage/xml/coverage.xml --cov-report=html:/home/glue_user/workspace/volume/coverage/html --cov-report=term-missing --cov-branch
USER root
ENTRYPOINT ["/home/glue_user/workspace/copy-volume.sh"]
#Build:
FROM base as build
RUN ["mkdir", "-m", "777", "-p", "/home/glue_user/workspace/volume/distributions"]
RUN ["chmod", "-R", "777", "/home/glue_user/workspace/volume"]
WORKDIR /home/glue_user/workspace
COPY ./MANIFEST.in /home/glue_user/workspace/
COPY ./requirements.txt requirements.txt
COPY tasks /home/glue_user/workspace/tasks/
RUN pip3 install --no-cache-dir build
RUN pip3 install wheel
RUN python3 -m build 
RUN python3 setup.py bdist_wheel
RUN pip3 wheel -r requirements.txt -w dist/
RUN cp -a dist/*.whl volume/distributions/
RUN chmod -R 777 volume/
# COPY --from=jars target/dependency/*.jar volume/distributions/ -- TODO: add later
USER root
ENTRYPOINT ["/home/glue_user/workspace/copy-volume.sh"]
