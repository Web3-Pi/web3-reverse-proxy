printheader()
{
	printf "\n"
	printf %"$COLUMNS"s |tr " " "="
	printf "\n$1\n"
	printf %"$COLUMNS"s |tr " " "="
	printf "\n"
}

printheader "Formatting"
python -m isort .
python -m black .
printheader "Lint check"
python -m pylint ./web3_reverse_proxy
printheader "Static typing check"
python -m mypy .
printheader "Unit tests"
python -m pytest

