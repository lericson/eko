Request Replay
==============

Oftentimes in development, one finds oneself in a situation where it'd
convenient to simply replay a request.

What I'm thinking is some way of doing this from the client, without involving
the server. The problem is that this would involve some sort of front-end for
the client, so perhaps this needs to be done first.

A GUI application could do this quite easily by saving the requests in some
sort of LRU structure, and perhaps you'd even be able to save requests.
