def matching_email_domains(args):
	"""prints emails developers, but pruned to just matching domains"""
	ids = []
	with model.db_context() as db:
		email_data = [(email.id, email.email.split('@')[-1], email.developer_id) for email in db.query(model.Email)]
		developer_data = {
			developer.id: lib.get_domain(developer.website)
				for developer in db.query(model.Developer).filter(model.Developer.website != None)
		}

		for (_id, email_domain, developer_id) in email_data:
			developer_domain = developer_data[developer_id]
			if developer_domain == email_domain:
				ids.append(_id)

	id_str = ",".join([str(i) for i in ids])
	q = _emails_q(where=f'email.id in ({id_str})')

	mysql_q(q, args)




def forums(args):
	"""lists forums and some dev info."""
	q = """
select
	developer.name,
	developer.created_at,
	forum_page.url
from developer
	join forum_page on
		forum_page.developer_id = developer.id
order by forum_page.created_at {order}
"""
	mysql_q(q, args)


def tags(args):
	"""lists developers from games"""
	q = """
select
	developer.name as developer,
	developer.created_at,
	game.name as game
from developer
	join game on
		game.developer_id = developer.id
order by game.created_at {order}
"""
	mysql_q(q, args)


def emails(args):
	"""lists emails for developers"""
	q = """
select
	email.email,
	developer.name
from email
	join developer on email.developer_id = developer.id
order by email.created_at {order}
"""
	mysql_q(q, args)

def whisky(args):
	"""lists whiskys"""
	q = """
select
	*
from whisky
order by created_at {order}
"""
	mysql_q(q, args)


def _emails_q(where=None):
	"""query for email, game, developer join,
reused in multiple commands"""
	q = """
	select
		email,
		developer_name,
		game.name,
		developer_site,
		email.developer_id,
		cnt from
		(select
			developer.name as developer_name,
			developer.id as developer_id,
			developer.website as developer_site,
			cnt from
			(select
				developer_id,
				count(*) as cnt
			from email
			group by developer_id
			) inr
		join developer
			on developer.id = inr.developer_id
		) otr
		join email
			on email.developer_id = otr.developer_id
		join game
			on game.developer_id = otr.developer_id
	"""
	if where:
		q += f"\nwhere {where}\n"
	q += 'order by cnt {order}'
	return q


def email_devs(args):
	q = _emails_q()
	mysql_q(q, args)


