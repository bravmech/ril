select content, state, added from items as I
join users as U
where I.user_id = U.id and U.name = 'brav' and I.state = 'unread';
