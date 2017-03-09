if [ $TRAVIS_PYTHON_VERSION = "2.7" ] && [ $TRAVIS_BRANCH = "master" ] && "$TRAVIS_PULL_REQUEST" == "false"]; then
  coverage run test_everything.py test_as_site-package
  coverage html
fi
