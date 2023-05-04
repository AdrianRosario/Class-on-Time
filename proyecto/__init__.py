import mailbox
from flask import Flask

app = Flask(__name__)
app.secret_key = "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"



import proyecto.views
import proyecto.models 