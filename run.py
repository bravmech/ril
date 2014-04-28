from ril import app, db

db.create_all()
db.session.commit()
app.run(debug=True)
