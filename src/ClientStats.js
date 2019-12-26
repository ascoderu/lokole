import React from 'react';
import { Card, Empty, Icon, List, Popconfirm, notification } from 'antd';
import axios from 'axios';

class ClientStats extends React.Component {
  state = {
    clients: [],
    isDeleting: {},
    isLoading: true,
  };

  get _client() {
    return axios.create({
      baseURL: this.props.settings.serverEndpoint,
      auth: {
        username: this.props.settings.githubUsername,
        password: this.props.settings.githubAccessToken,
      },
    });
  }

  get _isEnabled() {
    return this.props.settings.githubUsername && this.props.settings.githubAccessToken;
  }

  _fetchClients = async () => {
    let response;
    try {
      response = await this._client.get('/api/email/register/');
    } catch (e) {
      notification.error({
        message: 'Unable to fetch clients',
        description: e.response.data || e.message,
      });
      return;
    }

    this.setState({
      clients: response.data.clients.sort(),
      isLoading: false,
    });
  }

  _deleteClient = (domain) => () => {
    const setDeleting = (value, callback) => {
      this.setState(prevState => ({
        isDeleting: {
          ...prevState.isDeleting,
          [domain]: value,
        },
      }), callback);
    };

    setDeleting(true, async () => {
      try {
        await this._client.delete(`/api/email/register/${domain}`)
          .then(this._fetchClients);
      } catch (e) {
        notification.error({
          message: `Unable to delete client ${domain}`,
          description: e.response.data || e.message,
        });
      }
      setDeleting(false);
    });
  };

  _renderListItem = ({ domain }) => {
    const isDeleting = this.state.isDeleting[domain];

    return (
      <List.Item key={domain}>
        <Card
          actions={[
            <Popconfirm
              title={<span>This will delete client <em>{domain}</em>.<br />Are you sure?</span>}
              cancelText="No, cancel."
              okText="Yes, delete!"
              onConfirm={isDeleting ? undefined : this._deleteClient(domain)}
              disabled={isDeleting}
            >
              <Icon type={isDeleting ? 'loading' : 'delete'} />
            </Popconfirm>,
          ]}
          style={{ textDecoration: isDeleting ? 'line-through' : undefined }}
        >
          {domain}
        </Card>
      </List.Item>
    );
  };

  componentDidMount() {
    if (this._isEnabled) {
      this._fetchClients();
    }
  }

  render() {
    if (!this._isEnabled) {
      return (
        <Empty description="Add Github access token in settings to view clients." />
      );
    }

    return (
      <List
        grid={{ gutter: 16, column: 4 }}
        itemLayout="vertical"
        loading={this.state.isLoading}
        dataSource={this.state.clients}
        renderItem={this._renderListItem}
      />
    );
  }
}

export default ClientStats;
