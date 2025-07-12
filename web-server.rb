require 'webrick'

# Define the document root
root = File.expand_path('./docs')

server = WEBrick::HTTPServer.new :Port => 8808, :DocumentRoot => root

trap 'INT' do server.shutdown end

server.start

