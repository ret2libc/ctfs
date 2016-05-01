# Opabina regalis

I worked on these challenges with @pagabuc for some time.
We compiled the Protocol Buffer and started playing with the first challenge.

## Token fetch

Just receiving the first request and forwarding it tells us:
```
reply {
  status: 200
  headers {
    key: "Server"
    value: "opabina-regalis.go"
  }
  body: "<h1>this isn\'t the token you\'re looking for</h1>"
}
```
Let's just changing the request uri with `/token` and you get the flag

## Downgrade attack

This time if we just forward the request we get this message:
```
reply {
  status: 401
  headers {
    key: "Server"
    value: "opabina-regalis.go"
  }
  headers {
    key: "WWW-Authenticate"
    value: "Digest realm=\"In the realm of hackers\",qop=\"auth\",nonce=\"38c004ab191ad188\",opaque=\"38c004ab191ad188\""
  }
  headers {
    key: "Content-Length"
    value: "12"
  }
  body: "Unauthorized"
}
```

It seems like there is Digest Authentication on the server. After looking
around on the Web we found out it was possible to do a, guess what, downgrade
attack. You just need to make the client believe the server requested a basic
authentication and wait for the client to send you the username and the
password in clear (well, they are encoded with base64).

Once you get username and password, you can reply to the server with the Digest
authorization header and use username and password to calculate the response
field (by looking at the RFC). You just need to ask for the page
'/protected/secret' to get the flag.

## Redirect

You can see again a Digest authentication, but trying the downgrade attack
doesn't work this time (of course).

Simply forwarding the messages from the server to the client, we arrive to a
page that says it's not the token we're looking for. We can change the uri of
the first request with '/protected/secret' and get the flag.

## SSL Stripping

Looking at the first request we can see it's asking for the root page and it
returns an HTML page. We can save and open it to see there's a form where we
need to fill email and password. The form is submitted to
`https://elided/user/sign_in`. Just asking for the `/user/sign_in` page was
enough to get the flag.

## Input Validation

Looking at the first messages it seems like this challenge is really similar to
the Downgrade attack ones, so we reused the same script and we ended up in the
`/protected/joke` page. Considering we probably want to go again to
`/protected/token`, we can change the uri of the request and get the flag.
