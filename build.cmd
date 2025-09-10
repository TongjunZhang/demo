echo "python setup.py build -vf ..."
python setup.py build -vf
echo "python setup.py bdist_wheel ..."
python setup.py bdist_wheel
echo "aws s3 cp..."
aws s3 cp dist/cci-eap-edmdq-marketo-0.1-py3-none-any.whl s3://aws-glue-assets-875847150178-us-east-2/library/cci-eap-edmdq-marketo-0.1-py3-none-any.whl
echo "done"
