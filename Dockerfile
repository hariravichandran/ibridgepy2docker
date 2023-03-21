FROM jupyter/base-notebook:b86753318aa1

RUN pip install numpy pandas matplotlib cufflinks requests

CMD ["start-notebook.sh"]
