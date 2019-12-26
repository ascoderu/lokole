import React from 'react';
import { Card, Empty, Icon, List, Popconfirm, notification } from 'antd';
import axios from 'axios';

class ClientCard extends React.Component {
  state = {
    isDeleting: false,
    isFetchingPendingEmails: false,
    numPendingEmails: null,
  };

  _onClickDelete = async () => {
    if (this.state.isDeleting) {
      return;
    }

    this.setState({ isDeleting: true });
    await this.props.onDelete(this.props.domain);
    this.setState({ isDeleting: false });
  };

  _onClickFetchPendingEmails = async () => {
    if (this.state.isFetchingPendingEmails) {
      return;
    }

    this.setState({ isFetchingPendingEmails: true });
    const numPendingEmails = await this.props.fetchNumPendingEmails(this.props.domain);
    this.setState({ isFetchingPendingEmails: false, numPendingEmails });
  };

  render() {
    return (
      <Card
        actions={[
          <Popconfirm
            title={<span>This will delete client <em>{this.props.domain}</em>.<br />Are you sure?</span>}
            cancelText="No, cancel."
            okText="Yes, delete!"
            onConfirm={this._onClickDelete}
            disabled={this.state.isDeleting}
          >
            <Icon type={this.state.isDeleting ? 'loading' : 'delete'} />
          </Popconfirm>,
          <div>
            <Icon
              type={this.state.isFetchingPendingEmails ? 'loading' : 'mail'}
              onClick={this._onClickFetchPendingEmails}
            />
            {this.state.numPendingEmails != null && <span>&nbsp;{this.state.numPendingEmails}</span>}
          </div>,
        ]}
        style={{ textDecoration: this.state.isDeleting ? 'line-through' : undefined }}
      >
        {this.props.domain}
      </Card>
    );
  }
}

class ClientStats extends React.Component {
  state = {
    clients: [],
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
        description: (e.response && e.response.data) || e.message,
      });
      return;
    }

    this.setState({
      clients: response.data.clients.sort(),
      isLoading: false,
    });
  }

  _deleteClient = async (domain) => {
    try {
      await this._client.delete(`/api/email/register/${domain}`)
        .then(this._fetchClients);
    } catch (e) {
      notification.error({
        message: `Unable to delete client ${domain}`,
        description: (e.response && e.response.data) || e.message,
      });
    }
  };

  _fetchNumPendingEmails = async (domain) => {
    try {
      const response = await this._client.get(`/api/email/metrics/pending/${domain}`);
      return response.data.pending_emails;
    } catch (e) {
      notification.error({
        message: `Unable to fetch pending emails for client ${domain}`,
        description: (e.response && e.response.data) || e.message,
      });
      return null;
    }
  };

  _renderListItem = ({ domain }) => {
    return (
      <List.Item key={domain}>
        <ClientCard
          domain={domain}
          onDelete={this._deleteClient}
          fetchNumPendingEmails={this._fetchNumPendingEmails}
        />
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
